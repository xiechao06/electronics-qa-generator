"""DeepSeek chat-completions provider client.

All configuration comes from a ``.env`` file in the project root or cwd.
No third-party HTTP dependencies — uses stdlib ``urllib`` + ``json`` only.

Environment / env-file keys:
  ``DEEPSEEK_API_KEY``   — required to be "available"
  ``DEEPSEEK_BASE_URL``  — default ``https://api.deepseek.com``
  ``DEEPSEEK_MODEL``     — default ``deepseek-v4-pro``
"""

from __future__ import annotations

import json
import os
import pathlib
import urllib.error
import urllib.request
from typing import Any


# ---------------------------------------------------------------------------
# Lightweight .env parser (stdio-only; no python-dotenv dependency)
# ---------------------------------------------------------------------------


def _find_dotenv() -> pathlib.Path | None:
    """Locate the ``.env`` file, searching project root then cwd."""
    candidates = [
        pathlib.Path(__file__).resolve().parent.parent.parent.parent / ".env",  # project root
        pathlib.Path.cwd() / ".env",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def _parse_dotenv(path: pathlib.Path | None) -> dict[str, str]:
    """Parse a simple ``KEY=value`` dotenv file (no quoting, no escapes)."""
    if path is None:
        return {}
    out: dict[str, str] = {}
    for raw in path.read_text(errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip()
        if k:
            out[k] = v
    return out


def _read_config() -> dict[str, str]:
    """Return merged configuration from ``.env`` file.

    Environment variables take precedence over ``.env`` entries (so a CI
    workflow can inject the key without touching the project tree).
    """
    dotenv = _find_dotenv()
    cfg = _parse_dotenv(dotenv)
    # Let env vars override .env values
    for varname in ("DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL"):
        val = os.environ.get(varname)
        if val is not None:
            cfg[varname] = val
    return cfg


# ---------------------------------------------------------------------------
# DeepSeekError
# ---------------------------------------------------------------------------


class DeepSeekError(Exception):
    """Error raised for any provider failure (network, HTTP, JSON)."""

    def __init__(self, message: str, *, status: int | None = None):
        super().__init__(message)
        self.status = status


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_DEFAULT_BASE_URL = "https://api.deepseek.com"
_DEFAULT_MODEL = "deepseek-v4-pro"
_DEFAULT_TIMEOUT_SEC = 30


def is_available() -> bool:
    """Return True when ``DEEPSEEK_API_KEY`` is configured."""
    return bool(_read_config().get("DEEPSEEK_API_KEY"))


def complete(
    system_prompt: str,
    user_message: str,
    *,
    temperature: float = 0.0,
    max_tokens: int = 1024,
    timeout: float | None = None,
) -> str:
    """Call the DeepSeek chat-completions API and return the assistant content.

    Parameters
    ----------
    system_prompt : str
        System-level instruction.
    user_message : str
        User prompt.
    temperature : float
        Sampling temperature (default 0.0 for deterministic output).
    max_tokens : int
        Maximum tokens in the response.
    timeout : float or None
        Request timeout in seconds (default internal timeout).

    Returns
    -------
    str
        The assistant's text content.

    Raises
    ------
    DeepSeekError
        For any transport, HTTP, or JSON failure.
    """
    cfg = _read_config()
    api_key = cfg.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise DeepSeekError("DEEPSEEK_API_KEY not configured")

    base_url = cfg.get("DEEPSEEK_BASE_URL", _DEFAULT_BASE_URL).rstrip("/")
    model = cfg.get("DEEPSEEK_MODEL", _DEFAULT_MODEL)
    url = f"{base_url}/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    timeout_val = timeout if timeout is not None else _DEFAULT_TIMEOUT_SEC

    try:
        with urllib.request.urlopen(req, timeout=timeout_val) as resp:  # type: ignore[attr-defined]
            body = resp.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise DeepSeekError(str(exc)) from exc

    try:
        result = json.loads(body)
    except json.JSONDecodeError as exc:
        raise DeepSeekError(f"invalid JSON response: {exc}") from exc

    # Check for API-level error
    if "error" in result:
        err = result["error"]
        msg = err.get("message", str(err))
        raise DeepSeekError(msg)

    choices = result.get("choices")
    if not choices or not isinstance(choices, list):
        raise DeepSeekError("response missing 'choices' array")

    first = choices[0]
    message = first.get("message")
    if not isinstance(message, dict):
        raise DeepSeekError("response missing 'message' object")

    content = message.get("content")
    if not isinstance(content, str):
        raise DeepSeekError("response missing string 'content'")

    return content


# ---------------------------------------------------------------------------
# Vision provider (Ollama-hosted VLM via OpenAI-compatible endpoint)
# ---------------------------------------------------------------------------

_VISION_BASE_URL_DEFAULT = "http://localhost:11434/v1"
_VISION_MODEL_DEFAULT = "deepseek-vl2-tiny"


def is_vision_available() -> bool:
    """Return True when a VISION_BASE_URL is configured."""
    cfg = _read_config()
    return bool(cfg.get("VISION_BASE_URL") or True)  # always has a default


def complete_vision(
    system_prompt: str,
    user_prompt: str,
    image_path: str,
    *,
    timeout: float | None = None,
) -> str:
    """Send a prompt + base64-encoded image to a VLM.

    Uses the OpenAI-compatible ``/v1/chat/completions`` endpoint with an
    ``image_url`` content part containing the PNG as a base64 data URI.

    Configured via ``.env``:
      ``VISION_BASE_URL`` — default ``http://localhost:11434/v1``
      ``VISION_MODEL``  — default ``deepseek-vl2-tiny``

    Returns an empty string on any failure (pass-through semantics).
    """
    import base64
    from pathlib import Path

    cfg = _read_config()
    base_url = cfg.get("VISION_BASE_URL", _VISION_BASE_URL_DEFAULT).rstrip("/")
    model = cfg.get("VISION_MODEL", _VISION_MODEL_DEFAULT)
    url = f"{base_url}/chat/completions"

    # Read and encode the image
    img_path = Path(image_path)
    if not img_path.exists():
        return ""
    img_bytes = img_path.read_bytes()
    img_b64 = base64.b64encode(img_bytes).decode("ascii")
    data_uri = f"data:image/png;base64,{img_b64}"

    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": data_uri},
                    },
                ],
            },
        ],
        "temperature": 0.0,
        "max_tokens": 256,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")

    timeout_val = timeout if timeout is not None else 30.0

    try:
        with urllib.request.urlopen(req, timeout=timeout_val) as resp:
            body = resp.read().decode("utf-8")
    except Exception:
        return ""

    try:
        result = json.loads(body)
        choices = result.get("choices")
        if choices and isinstance(choices, list):
            msg = choices[0].get("message", {})
            content = msg.get("content", "")
            if isinstance(content, str):
                return content
    except json.JSONDecodeError, KeyError, IndexError, TypeError:
        pass

    return ""
