## 1. Fix vision provider wiring

- [x] 1.1 In `validation/cli_handler.py`, replace `vision_provider = True` with `from ..llm.provider import complete_vision; vision_provider = complete_vision`
- [x] 1.2 In `validation/report.py`, update `from_items()` to accept `vision_provider` as `Callable | None` and pass it directly (no sentinel conversion)
- [x] 1.3 In `validation/visual_checks.py`, remove any `True`-sentinel handling from `_run_vision_check` (the `provider is None` fallback already handles direct use)

## 2. Documentation

- [x] 2.1 Add `VISION_BASE_URL` and `VISION_MODEL` entries to `.env.example` with defaults documented
- [x] 2.2 Add an "Ollama Setup" section to the README or a relevant config doc covering: install Ollama, start service, pull `deepseek-vl2-tiny`

## 3. Verify

- [x] 3.1 Run `uv run eqa validate <topology> --seed 0 --visual` — confirm vision checks actually invoke the VLM (check output for WARN/PASS from topology_match and label_visibility)
- [x] 3.2 Run `uv run pytest tests/` — confirm no regressions from wiring changes
- [x] 3.3 Test pass-through behavior when Ollama is stopped: confirm checks return PASS without errors
