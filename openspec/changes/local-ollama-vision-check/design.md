## Context

The `validate` CLI subcommand accepts a `--visual` flag to run
vision-model quality checks (topology-match, label-visibility) on
rendered schematic PNGs. The vision provider already exists in
`llm/provider.py` as `complete_vision()`, which hits an
Ollama-hosted `deepseek-vl2-tiny` model at `http://localhost:11434/v1`.

**Bug**: The CLI wiring passes `vision_provider = True` (a boolean)
instead of the `complete_vision` callable. The `_run_vision_check`
function in `visual_checks.py` falls back to `complete_vision` only
when `provider is None`, but `True` is not `None`. Calling `True()`
raises `TypeError`, which is caught and silently returns PASS — so
every vision check silently does nothing.

The DeepSeek cloud API (`deepseek-v4-pro`, `deepseek-v4-flash`) has
no vision model, so a cloud path is not possible.

## Goals / Non-Goals

**Goals:**
- Fix the `vision_provider` wiring so `--visual` actually invokes the VLM
- Make vision checks pass-through (PASS) when Ollama is unavailable
- Document the Ollama setup requirements

**Non-Goals:**
- Changing the DeepSeek text-completions provider (stays as-is for humanization)
- Adding a cloud-based vision provider
- Changing the check logic itself (prompts, verdict parsing)
- Adding new visual checks

## Decisions

### 1. Pass the callable directly instead of using a boolean sentinel

**Decision**: In `cli_handler.py`, replace `vision_provider = True` with
`vision_provider = complete_vision`. In `report.py`, accept
`vision_provider` as `Callable | None` and forward it.

**Rationale**: The boolean sentinel is a failure point — it requires every
consumer to know to reinterpret `True`. Passing the actual callable removes
the ambiguity and the silent failure.

**Alternative considered**: Keep `True` sentinel and add a check in
`_run_vision_check` for `provider is True`. Rejected because it pushes
the sentinel logic further from the decision point and adds unnecessary
indirection for future check authors.

### 2. Keep `_run_vision_check` fallback logic intact

**Decision**: When `provider=None` (programmatic use without CLI), still
fall back to `complete_vision`. Remove the dead path where `True` could
be passed.

### 3. Document Ollama setup in project

**Decision**: Add `VISION_BASE_URL` and `VISION_MODEL` to `.env.example`
and mention the required setup steps.

## Risks / Trade-offs

- **Ollama not installed/running** → `complete_vision` returns `""` on
  connection failure; `_run_vision_check` treats empty response as
  "VLM unavailable" and returns PASS. This is intentional — vision checks
  are advisory (WARN), never blocking.
- **Network latency** → Ollama runs locally, so latency is minimal (~1-2s).
  Cache (VisualCheckCache) avoids re-checking the same image across repeated
  validate runs.
- **Model not pulled** → same as "not running"; passes through.
