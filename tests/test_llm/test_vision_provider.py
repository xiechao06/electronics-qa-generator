"""Tests for llm/provider.py complete_vision()."""

from __future__ import annotations

import json
import urllib.request

from electronics_qa_generator.llm.provider import complete_vision, is_vision_available


class TestCompleteVision:
    def test_encodes_image_base64(self, tmp_path, monkeypatch):
        """Verify the payload includes a base64 data URI for the image."""
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG\x00fake")

        captured = {}

        class FakeResponse:
            def read(self):
                return json.dumps(
                    {
                        "choices": [{"message": {"content": "PASS"}}],
                    }
                ).encode("utf-8")

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        def _capture(req, *args, **kwargs):
            captured["data"] = json.loads(req.data)
            return FakeResponse()

        monkeypatch.setattr(urllib.request, "urlopen", _capture)

        result = complete_vision("sys", "user", str(img))
        assert result == "PASS"
        payload = captured["data"]
        messages = payload["messages"]
        user_msg = messages[1]
        content = user_msg["content"]
        assert content[0]["type"] == "text"
        assert content[1]["type"] == "image_url"
        assert "base64" in content[1]["image_url"]["url"]

    def test_returns_empty_on_missing_image(self):
        result = complete_vision("sys", "user", "/nonexistent/path.png")
        assert result == ""

    def test_returns_empty_on_http_error(self, tmp_path, monkeypatch):
        img = tmp_path / "test.png"
        img.write_bytes(b"png")

        def _raise(*args, **kwargs):
            raise OSError("connection refused")

        monkeypatch.setattr(urllib.request, "urlopen", _raise)
        result = complete_vision("sys", "user", str(img))
        assert result == ""


class TestIsVisionAvailable:
    def test_returns_true(self):
        # Always returns True since there's a default VISION_BASE_URL
        assert is_vision_available() is True
