## Why

Visual QA-item checks (topology verification, label readability) are
already implemented with an Ollama-backed `deepseek-vl2-tiny` provider,
but the CLI wiring passes a boolean sentinel (`True`) instead of the
callable — causing every vision check to silently fail with
`'bool' object is not callable`. Meanwhile, the DeepSeek API only
supports `deepseek-v4-pro` and `deepseek-v4-flash` (no vision model),
so the cloud path is dead. Fixing the wiring makes vision checks
actually work with the already-implemented local Ollama provider.

## What Changes

- Fix `vision_provider` passing in `validation/cli_handler.py` and
  `report.py` — pass `complete_vision` callable instead of `True`
- Update `_run_vision_check` in `visual_checks.py` to treat `True`
  as a fallback sentinel (for compatibility) or remove the sentinel
  entirely
- Document `VISION_BASE_URL` / `VISION_MODEL` env vars in project
  README or `.env.example`
- No **BREAKING** changes — fixes existing but broken behavior

## Capabilities

### New Capabilities

- `local-vision-checks`: End-to-end vision-model quality checks on
  schematic images using Ollama-hosted `deepseek-vl2-tiny`, with
  pass-through semantics when the VLM is unavailable.

### Modified Capabilities

<!-- None — this fixes existing code without changing spec-level behavior -->

## Impact

- `src/electronics_qa_generator/validation/cli_handler.py` — send
  actual callable instead of `True`
- `src/electronics_qa_generator/validation/visual_checks.py` — handle
  `True` sentinel or remove sentinel usage
- `src/electronics_qa_generator/llm/provider.py` — no changes needed
  (`complete_vision` already uses Ollama)
- Documentation: add `.env.example` entry for vision vars
