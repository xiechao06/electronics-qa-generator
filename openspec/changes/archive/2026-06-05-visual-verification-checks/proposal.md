## Why

The static verifier and LLM checks cover text quality, but a multimodal benchmark must
also verify that the schematic **images** are correct. When an RC low-pass schematic
accidentally renders as high-pass, or component labels are illegible in the PNG, the
dataset quality suffers in ways no text-only check can catch.

## What Changes

- Add a `complete_vision()` function to `llm/provider.py` that sends a base64-encoded
  PNG image to an Ollama-hosted vision model via the OpenAI-compatible
  `/v1/chat/completions` endpoint. Configured via `.env`: `VISION_BASE_URL`
  (default `http://localhost:11434/v1`), `VISION_MODEL` (default
  `deepseek-vl2-tiny:nocaption`). No new HTTP dependency — reuses existing `urllib`
  pattern.
- Add 2 visual check functions to `validation/visual_checks.py`:
  1. **Schematic–topology match** — sends the schematic PNG + topology name to the
     VLM; asks "Does this schematic show a {topology}?" Returns WARN on mismatch.
  2. **Label visibility** — sends the PNG; asks "Are all component labels clearly
     readable?" Returns WARN if labels are obscured, clipped, or illegible.
- Both checks follow the same `CheckResult`/`Verdict` interface and are advisory
  (WARN, never FAIL).
- Wire into `eqa validate --visual` and `eqa questions --verify --visual`. Requires
  `--render` to have produced the schematic PNG first.
- Cache results by schematic path hash for deterministic reruns.

## Capabilities

### New Capabilities
- `vision-provider`: A `complete_vision()` function extending the existing LLM
  provider to send base64-encoded images to an Ollama-hosted VLM via the
  OpenAI-compatible `/v1/chat/completions` endpoint.
- `visual-verification-checks`: Two VLM-assisted QA-item quality checks (topology
  match, label visibility) operating on rendered schematic PNGs, following the
  CheckResult/Verdict interface, with caching and pass-through fallback.

### Modified Capabilities
<!-- None -->

## Impact

- **Code**: `llm/provider.py` (+ `complete_vision()`); `validation/visual_checks.py`
  (new, 2 check functions + `VISUAL_CHECKS`); `validation/checks.py` (+ import);
  `validation/report.py` (+ visual check integration); `validation/cli_handler.py`
  (+ `--visual`); `questions/cli_handler.py` (+ `--visual`); `cli.py` (+ flag).
- **Dependencies**: Ollama with `deepseek-vl2-tiny` model pulled (`ollama pull
  deepseek-vl2-tiny:latest`). No new Python packages.
- **Invariant**: Visual checks are advisory (WARN). Unavailable VLM → PASS.
