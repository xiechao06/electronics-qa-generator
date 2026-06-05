## 1. Vision provider

- [x] 1.1 Add `complete_vision()` to `src/electronics_qa_generator/llm/provider.py`:
  accepts `(system_prompt, user_prompt, image_path)`, reads PNG as base64, constructs
  OpenAI-compatible vision payload, POSTs to `{VISION_BASE_URL}/v1/chat/completions`.
  Config via `.env`: `VISION_BASE_URL` (default `http://localhost:11434/v1`),
  `VISION_MODEL` (default `deepseek-vl2-tiny`). Returns response text or `""` on
  failure.
- [x] 1.2 Add `is_vision_available()` helper checking VISION_BASE_URL reachability.

## 2. Visual check functions

- [x] 2.1 Add `src/electronics_qa_generator/validation/visual_checks.py` with
  `check_topology_match(item, schematic_path, *, provider)` and
  `check_label_visibility(item, schematic_path, *, provider)`. Both return
  CheckResult (WARN on issue, PASS otherwise). Skip with PASS when
  `schematic_path` is None.
- [x] 2.2 Implement topology-match prompt: system prompt describes circuit symbols
  (zigzag=resistor, plates=capacitor, coil=inductor, triangle+bar=diode); user
  prompt asks "Does this schematic match the topology '{topology}'?".
- [x] 2.3 Implement label-visibility prompt: "Are all component reference labels
  (R1, C1, etc.) and values clearly readable in this schematic image?".
- [x] 2.4 Wire caching by schematic_path hash.

## 3. Integration with validation pipeline

- [x] 3.1 Register `VISUAL_CHECKS` in `validation/checks.py`.
- [x] 3.2 Update `ValidationReport.from_items()` to accept `vision_provider` +
  `schematic_path` kwargs; run visual checks on items with a schematic.
- [x] 3.3 Update `validation/cli_handler.py` to pass `--visual` flag to
  `from_items()`.
- [x] 3.4 Update `questions/cli_handler.py` to accept `--visual` alongside
  `--verify`.

## 4. CLI integration

- [x] 4.1 Add `--visual` flag to `eqa validate` and `eqa questions` subparsers.

## 5. Tests

- [x] 5.1 Add `tests/test_validation/test_visual_checks.py`: test each check with
  a fake vision provider; test pass-through when schematic_path is None; test
  provider unavailability returns PASS.
- [x] 5.2 Add `tests/test_llm/test_vision_provider.py`: test base64 encoding,
  payload construction, empty response on failure.

## 6. Validation

- [x] 6.1 Run `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`; all
  must pass.
