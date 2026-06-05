"""Tests for llm/provider.py — DeepSeek API client."""

from __future__ import annotations

import io
import json
import pathlib
import urllib.error
import urllib.request

import pytest

from electronics_qa_generator.llm.provider import (
    DeepSeekError,
    _DEFAULT_BASE_URL,
    _DEFAULT_MODEL,
    _find_dotenv,
    _parse_dotenv,
    _read_config,
    complete,
    is_available,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_fake_response(content: str, status: int = 200) -> io.BytesIO:
    """Return a BytesIO that urlopen can read."""
    body = json.dumps(
        {
            "choices": [{"message": {"content": content}}],
        }
    ).encode("utf-8")
    return io.BytesIO(body)


def _patch_urlopen(monkeypatch, content: str = "hello", status: int = 200):
    """Replace urllib.request.urlopen with a fake callable."""

    class FakeResponse:
        def __init__(self, *args, **kwargs):
            pass

        def read(self):
            return json.dumps(
                {
                    "choices": [{"message": {"content": content}}],
                }
            ).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(urllib.request, "urlopen", FakeResponse)


# ---------------------------------------------------------------------------
# .env parser tests
# ---------------------------------------------------------------------------


class TestDotenvParser:
    def test_parse_simple(self, tmp_path):
        p = tmp_path / ".env"
        p.write_text("DEEPSEEK_API_KEY=sk-test123\nDEEPSEEK_MODEL=deepseek-v4-pro\n")
        result = _parse_dotenv(p)
        assert result == {"DEEPSEEK_API_KEY": "sk-test123", "DEEPSEEK_MODEL": "deepseek-v4-pro"}

    def test_parse_skips_comments_and_blanks(self, tmp_path):
        p = tmp_path / ".env"
        p.write_text("# comment\n  \nDEEPSEEK_API_KEY=foo\n")
        result = _parse_dotenv(p)
        assert result == {"DEEPSEEK_API_KEY": "foo"}

    def test_parse_strips_whitespace(self, tmp_path):
        p = tmp_path / ".env"
        p.write_text("  DEEPSEEK_API_KEY = sk-bar  \n")
        result = _parse_dotenv(p)
        assert result == {"DEEPSEEK_API_KEY": "sk-bar"}

    def test_parse_none(self):
        assert _parse_dotenv(None) == {}


class TestDotenvFind:
    def test_find_in_cwd(self, tmp_path, monkeypatch):
        p = tmp_path / ".env"
        p.write_text("DEEPSEEK_API_KEY=sk-test\n")
        monkeypatch.chdir(tmp_path)
        found = _find_dotenv()
        assert found is not None
        assert found.name == ".env"

    def test_not_found(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert _find_dotenv() is None


class TestReadConfig:
    def test_reads_from_dotenv(self, tmp_path, monkeypatch):
        p = tmp_path / ".env"
        p.write_text("DEEPSEEK_API_KEY=sk-fromfile\nDEEPSEEK_MODEL=custom-model\n")
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)
        monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)
        cfg = _read_config()
        assert cfg["DEEPSEEK_API_KEY"] == "sk-fromfile"
        assert cfg["DEEPSEEK_MODEL"] == "custom-model"

    def test_env_override(self, tmp_path, monkeypatch):
        p = tmp_path / ".env"
        p.write_text("DEEPSEEK_API_KEY=sk-fromfile\n")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-fromenv")
        cfg = _read_config()
        assert cfg["DEEPSEEK_API_KEY"] == "sk-fromenv"


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------


class TestIsAvailable:
    def test_true_with_key(self, tmp_path, monkeypatch):
        p = tmp_path / ".env"
        p.write_text("DEEPSEEK_API_KEY=sk-123\n")
        monkeypatch.chdir(tmp_path)
        assert is_available() is True

    def test_false_without_key(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        assert is_available() is False


# ---------------------------------------------------------------------------
# complete() tests
# ---------------------------------------------------------------------------


class TestComplete:
    def test_returns_content(self, tmp_path, monkeypatch):
        p = tmp_path / ".env"
        p.write_text("DEEPSEEK_API_KEY=sk-ok\n")
        monkeypatch.chdir(tmp_path)
        _patch_urlopen(monkeypatch, content="rewritten question text")

        result = complete("system", "user")
        assert result == "rewritten question text"

    def test_raises_when_no_key(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        with pytest.raises(DeepSeekError, match="not configured"):
            complete("sys", "usr")

    def test_raises_on_url_error(self, tmp_path, monkeypatch):
        p = tmp_path / ".env"
        p.write_text("DEEPSEEK_API_KEY=sk-err\n")
        monkeypatch.chdir(tmp_path)

        def _raise(*args, **kwargs):
            raise urllib.error.URLError("connection refused")

        monkeypatch.setattr(urllib.request, "urlopen", _raise)
        with pytest.raises(DeepSeekError, match="connection refused"):
            complete("sys", "usr")

    def test_raises_on_bad_json(self, tmp_path, monkeypatch):
        p = tmp_path / ".env"
        p.write_text("DEEPSEEK_API_KEY=sk-bad\n")
        monkeypatch.chdir(tmp_path)

        class BadJsonResponse:
            def __init__(self, *args, **kwargs):
                pass

            def read(self):
                return b"not json"

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        monkeypatch.setattr(urllib.request, "urlopen", BadJsonResponse)
        with pytest.raises(DeepSeekError, match="invalid JSON"):
            complete("sys", "usr")

    def test_raises_on_api_error(self, tmp_path, monkeypatch):
        p = tmp_path / ".env"
        p.write_text("DEEPSEEK_API_KEY=sk-api-err\n")
        monkeypatch.chdir(tmp_path)

        class ErrorResponse:
            def __init__(self, *args, **kwargs):
                pass

            def read(self):
                return json.dumps({"error": {"message": "rate limited"}}).encode("utf-8")

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        monkeypatch.setattr(urllib.request, "urlopen", ErrorResponse)
        with pytest.raises(DeepSeekError, match="rate limited"):
            complete("sys", "usr")

    def test_defaults_applied(self, tmp_path, monkeypatch):
        p = tmp_path / ".env"
        p.write_text("DEEPSEEK_API_KEY=sk-ok\n")
        monkeypatch.chdir(tmp_path)

        captured = {}

        def _capture(req, *args, **kwargs):
            captured["url"] = req.full_url
            captured["data"] = json.loads(req.data)

            class R:
                def __init__(self, *a, **kw):
                    pass

                def read(self):
                    return json.dumps(
                        {
                            "choices": [{"message": {"content": "ok"}}],
                        }
                    ).encode("utf-8")

                def __enter__(self):
                    return self

                def __exit__(self, *a):
                    pass

            return R()

        monkeypatch.setattr(urllib.request, "urlopen", _capture)

        complete("sys", "usr")

        assert _DEFAULT_BASE_URL.rstrip("/") + "/v1/chat/completions" in captured["url"]
        payload = captured["data"]
        assert payload["model"] == _DEFAULT_MODEL
        assert payload["temperature"] == 0.0

    def test_overrides_base_url_and_model(self, tmp_path, monkeypatch):
        p = tmp_path / ".env"
        p.write_text(
            "DEEPSEEK_API_KEY=sk-ok\n"
            "DEEPSEEK_BASE_URL=https://custom.api.com\n"
            "DEEPSEEK_MODEL=custom-model\n"
        )
        monkeypatch.chdir(tmp_path)

        captured = {}

        def _capture(req, *args, **kwargs):
            captured["url"] = req.full_url
            captured["data"] = json.loads(req.data)

            class R:
                def __init__(self, *a, **kw):
                    pass

                def read(self):
                    return json.dumps(
                        {
                            "choices": [{"message": {"content": "ok"}}],
                        }
                    ).encode("utf-8")

                def __enter__(self):
                    return self

                def __exit__(self, *a):
                    pass

            return R()

        monkeypatch.setattr(urllib.request, "urlopen", _capture)

        complete("sys", "usr")

        assert "https://custom.api.com/v1/chat/completions" in captured["url"]
        assert captured["data"]["model"] == "custom-model"

    def test_no_third_party_http_import(self):
        """Assert the provider module does not import httpx, requests, aiohttp, etc."""

        src = (
            pathlib.Path(__file__).parent.parent.parent
            / "src"
            / "electronics_qa_generator"
            / "llm"
            / "provider.py"
        )
        text = src.read_text()
        for banned in ("import httpx", "import requests", "import aiohttp", "import openai"):
            assert banned not in text, f"provider.py should not use {banned}"
