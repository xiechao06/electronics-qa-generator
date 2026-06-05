## Why

The static verifier catches deterministic errors (wrong answers, unit mismatches,
degenerate values) but cannot assess human-perceptible quality issues like phrasing
ambiguity, implicit answer leakage, or difficulty level. The Verifier backlog
reserves an LLM-assisted tier for these checks. We add it now using the same
DeepSeek `deepseek-v4-pro` provider already available from the humanization stage.

## What Changes

- Add 3 LLM-assisted checks to the validation subpackage, using the existing
  DeepSeek provider (`llm/provider.py`) for all calls:
  1. **Wording ambiguity** — LLM rates whether the question phrasing is ambiguous
     or requires circuit-specific knowledge beyond what's stated.
  2. **Semantic leakage** — LLM detects whether the question implicitly reveals
     its own answer (e.g., "Given the cutoff is 233 Hz, find the bandwidth").
  3. **Difficulty scoring** — LLM assigns a difficulty label (easy/medium/hard)
     based on question complexity and cognitive level.
- Each check is a function `check_*(item, provider) -> CheckResult`, following
  the same CheckResult/Verdict interface as static checks.
- Checks are opt-in and best-effort: unavailable provider → PASS (not FAIL), same
  as humanization.
- Wire into `eqa validate --llm` flag and `eqa questions --verify --llm`.
- Cache LLM responses by question text for deterministic reruns.

## Capabilities

### New Capabilities
- `llm-verification-checks`: Three LLM-assisted QA-item quality checks (wording
  ambiguity, semantic leakage, difficulty scoring) using the DeepSeek provider,
  with caching, pass-through fallback, and uniform CheckResult/Verdict interface.

### Modified Capabilities
<!-- None -->

## Impact

- **Code**: `src/electronics_qa_generator/validation/llm_checks.py` (new, 3 check
  functions); `validation/checks.py` (+ LLM_CHECKS registry);
  `validation/cli_handler.py` (+ `--llm` flag); `validation/report.py` (+ LLM
  check integration); `cli.py` (+ `--llm` on validate subcommand).
- **Dependencies**: None new — reuses `llm/provider.py` (DeepSeek via `.env`).
- **Invariant**: LLM checks are advisory only — a FAIL from an LLM check never
  blocks dataset assembly; they produce WARN-level verdicts.
