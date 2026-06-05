## Context

The static verifier (7 checks) catches deterministic errors. The backlog reserves
3 LLM-assisted checks for human-perceptible qualities: wording ambiguity, semantic
answer leakage, and difficulty scoring. The DeepSeek `deepseek-v4-pro` provider
(`llm/provider.py`) is already implemented and in use for question humanization —
these checks reuse the same infrastructure.

## Goals / Non-Goals

**Goals:**
- Add 3 LLM checks that follow the same `CheckResult`/`Verdict` interface as static
  checks, integrate seamlessly into `ValidationReport`, and are opt-in.
- Use the existing DeepSeek provider; no new API or dependency.
- LLM checks are advisory (WARN, never FAIL) — they inform but don't gate.
- Cache responses by question text for deterministic reruns.

**Non-Goals:**
- Making LLM checks required for CI (they're always optional).
- Multi-turn or chain-of-thought prompting (single completion per check).
- Batch API calls (each check is one call per item for simplicity).

## Decisions

### Decision: One combined prompt per check, not per question
Each check function sends a system prompt defining the task + a user message with
the question text (and answer for leakage/difficulty). One API call per check.
- **Why:** Simpler to implement, easier to cache, matches the humanization pattern.
- **Alternative considered:** Batch all 3 checks into one call. Rejected — harder
  to parse structured output from a single response.

### Decision: LLM checks always produce WARN on detection, never FAIL
The LLM is imperfect; false positives on ambiguity or leakage shouldn't block
dataset assembly. Static checks handle definitive errors; LLM checks are advisory.
- **Why:** Prevents LLM hallucination from breaking CI. Aligns with the project
  invariant that LLM never creates truth.

### Decision: Provider pass-through on unavailability
When `DEEPSEEK_API_KEY` is not configured, LLM checks return PASS immediately.
When the provider raises `DeepSeekError`, the check returns PASS with a note.
- **Why:** Same as humanization — opt-in, best-effort, never breaks the pipeline.

### Decision: Reuse `HumanizationCache` pattern for LLM check caching
A single `LLMCheckCache` keyed by `(check_name, question_text)` stores verdicts
as JSON. Checks are pure functions of the question text + answer, so caching is
deterministic.
- **Why:** Avoids duplicate API costs during development and re-runs.

## Risks / Trade-offs

- **LLM hallucinates a difficulty score** → Difficulty is always PASS verdict;
  incorrect difficulty labels are harmless noise.
- **Token costs for large batches** → Cache makes repeated runs cheap; for a 25-item
  run, 75 API calls can be expensive — the `--llm` flag is explicit opt-in.
- **Latency** → Each LLM call takes ~1-3s. With caching, first run is slow but
  subsequent runs are instant.

## Migration Plan

1. Add `validation/llm_checks.py` with 3 check functions + cache.
2. Register `LLM_CHECKS` in `validation/checks.py`.
3. Add `--llm` flag to `eqa validate` and `eqa questions --verify --llm`.
4. Update `ValidationReport.from_items()` to accept an optional provider + cache.
5. Add tests with fake provider.
- **Rollback:** Remove `--llm` flag; static checks continue as before.

## Open Questions

- Should difficulty scoring use a 3-point or 5-point scale? Start with 3 (easy/
  medium/hard); extend later if needed.
