## Context

The pipeline computes every answer deterministically (simulation → fact extraction →
CLEVR-style program). Question text today comes from fixed templates in
`questions/templates.py`, producing correct but stiff phrasing. The architecture
(`docs/architecture.md` §10) and plan (`docs/plan.md` §8) already reserve an **optional
LLM layer** for paraphrasing and explanations, gated by the non-negotiable invariant:

> The LLM never creates truth. Simulation establishes facts, code derives answers, and
> the LLM only paraphrases/explains/tags after the answer is fixed.

The `llm/` subpackage exists only as a docstring stub. `QAItem` already has an
`explanation: str | None` field. This change implements humanization against the
DeepSeek `deepseek-v4-pro` API as an opt-in stage, keeping default behavior and tests
fully offline and reproducible.

## Goals / Non-Goals

**Goals:**
- Reword finalized questions into natural, exam-style language using `deepseek-v4-pro`.
- Optionally generate explanations that reference the already-fixed answer.
- Guarantee deterministic answer fields are never mutated by the LLM (verify after).
- Zero new required dependencies (stdlib `urllib`/`json` for HTTP).
- Off by default; offline-safe pass-through when unconfigured or on failure.
- Deterministic caching so reruns are cheap and CI stays hermetic.

**Non-Goals:**
- Using the LLM to compute, choose, or validate any numeric answer or behavior label.
- Generating multiple-choice distractors (future work; this change only rewords the
  stem and writes explanations).
- Streaming responses, async batching, or multi-provider abstraction (single provider).
- Changing the `generate` pipeline command or any existing output when `--humanize` is
  absent.

## Decisions

### Decision: Layer humanization strictly after answer computation
Humanization consumes a fully-built `QAItem` and returns a new `QAItem`. The
deterministic fields (`answer`, `answer_value`, `unit`, `tolerance`, `choices`,
`program`) are copied from the input and re-asserted after the LLM call. The LLM is only
permitted to influence `question` and `explanation`.
- **Why:** Enforces the invariant structurally — the answer physically cannot come from
  the model because it is fixed before the call and compared after.
- **Alternative considered:** Ask the LLM to return the full item as JSON. Rejected:
  invites answer drift and parsing fragility.

### Decision: Prompt contract returns only reworded stem + explanation
The system prompt instructs the model to preserve all quantities, units, and numeric
references exactly, reword only the phrasing, and never state a different answer. The
user message carries the original question and (optionally) the known answer string for
explanation context. The response is parsed for two fields: `question` and
`explanation` (simple delimited or JSON-object response).
- **Why:** Narrow contract minimizes the model's ability to alter meaning.
- **Guard:** A post-call check rejects rewordings that drop/alter the unit token or the
  numeric answer string when those appear in the original; on rejection we keep the
  original question.

### Decision: Standard-library HTTP client with dotenv config (`provider.py`)
Use `urllib.request` + `json` to POST to the DeepSeek chat-completions endpoint. Config
from a `.env` file in the project root: `DEEPSEEK_API_KEY` (required to be
"available"), `DEEPSEEK_BASE_URL` (default DeepSeek endpoint), `DEEPSEEK_MODEL`
(default `deepseek-v4-pro`). The `.env` file is parsed manually (no `python-dotenv`
dependency) with a simple key-value reader in stdlib. Failures raise a single
`DeepSeekError`.
- **Why:** No new required dependency; keeps base install light per project tooling
  rules. Network only touched when `--humanize` is set and a key exists.
- **Alternative considered:** `httpx`/`openai` SDK or `python-dotenv`. Rejected for the
  MVP to avoid dependency weight; `.env` parsing is ~10 lines of stdlib. Can swap
  later behind the same `provider` seam.

### Decision: Deterministic pass-through fallback
`humanize_item` catches `DeepSeekError` and unavailability and returns the input item
unchanged. The CLI handler treats the whole stage as best-effort.
- **Why:** The pipeline must never break or become non-reproducible because of an
  optional polish step; tests run without network.

### Decision: Content-addressed cache (`llm/cache.py`)
Mirror the existing `simulation/cache.py` pattern: JSON file cache keyed by a hash of
`(original_question, model, options_signature)`. A stub/fake provider is injected in
tests.
- **Why:** Cheap reruns and deterministic CI; consistent with existing caching style.

### Decision: CLI integration via `--humanize` only
Add `--humanize` to the `questions` subparser; `run_questions` maps each item through
`humanize_item` when set. Output serialization gains the `explanation` field.
- **Why:** Smallest possible surface; default path is untouched and byte-identical.

## Risks / Trade-offs

- **LLM alters a number or unit despite instructions** → Post-call guard compares the
  answer string/unit token against the reworded text; on mismatch, keep the original
  question. Answer fields are never sourced from the model regardless.
- **Non-determinism across runs** → Caching plus `temperature=0` (or low) request
  parameter; tests use a fixed fake provider, never the live API.
- **Network/latency/cost when enabled** → Opt-in flag, bounded timeout, and cache.
  Default runs make zero calls.
- **Hidden dependency creep** → Enforce stdlib-only transport in the provider spec and a
  test asserting no third-party HTTP import.
- **Malformed model output** → Parse defensively; any parse failure falls back to the
  original question via the pass-through path.

## Migration Plan

1. Implement `llm/provider.py`, `llm/cache.py`, `llm/humanize.py` (additive).
2. Add `--humanize` to `cli.py` and branch in `questions/cli_handler.py`; add
   `explanation` to the emitted dict.
3. Add tests with a fake provider (success, answer-drift rejection, pass-through, cache
   hit) plus a default-behavior-unchanged test.
4. Document `.env` file setup (`DEEPSEEK_API_KEY`, optional `DEEPSEEK_BASE_URL` /
   `DEEPSEEK_MODEL`) in `README.md`; add `.env` to `.gitignore`.
- **Rollback:** Remove/ignore the `--humanize` flag; no stored data schema changes are
  required since `explanation` already exists on `QAItem`.

## Open Questions

- Exact DeepSeek base URL/path and request schema for `deepseek-v4-pro` (confirm against
  current DeepSeek API docs at implementation time; isolated in `provider.py`).
- `.env` file location: resolved from the project root (or current working directory
  fallback); documented in `README.md`.
- Response shape for the rewording contract (JSON object vs. delimited sections) — pick
  whichever the model follows most reliably; keep parsing tolerant.
