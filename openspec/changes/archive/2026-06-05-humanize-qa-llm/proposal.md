## Why

Generated questions currently use rigid, templated phrasing (e.g., "Find the −3 dB
cutoff frequency. Provide your answer in Hz, rounded to the nearest integer."). Real
benchmarks like MMMU use varied, natural, textbook/exam-style language. To raise the
linguistic quality and diversity of the dataset without ever compromising ground
truth, we add an optional LLM layer that **rewords** questions and **writes
explanations** *after* the deterministic answer is already fixed — calling the
DeepSeek `deepseek-v4-pro` API.

## What Changes

- Add an LLM humanization stage in the existing (stub) `llm/` subpackage that takes a
  fully-computed `QAItem` and returns a paraphrased question string plus an optional
  explanation, leaving `answer`, `answer_value`, `unit`, `tolerance`, `choices`, and
  `program` **byte-for-byte unchanged**.
- Add a provider client for the DeepSeek API (`deepseek-v4-pro`), configured via
  a `.env` file (`DEEPSEEK_API_KEY`, optional `DEEPSEEK_BASE_URL`/`DEEPSEEK_MODEL`),
  using only the Python standard library for HTTP so no new hard dependency is added.
- Add a deterministic, offline-safe fallback: when no API key is present or the call
  fails, items pass through unchanged so the pipeline never breaks and tests stay
  hermetic.
- Wire an opt-in `--humanize` flag into the `eqa questions` CLI; humanization is **off
  by default** to preserve current behavior and reproducibility.
- Preserve the core invariant with a post-humanization guard: the deterministic answer
  fields are re-asserted/compared after the LLM call; any drift is rejected and the
  original question is kept.
- Cache humanized results keyed by question content + model so reruns are cheap and
  deterministic.

## Capabilities

### New Capabilities
- `llm-humanization`: Reword a finalized `QAItem`'s question text and generate an
  optional explanation via an LLM, while guaranteeing the deterministic answer,
  units, tolerance, choices, and program are never altered. Covers the prompt
  contract, the answer-preservation guard, caching, and the offline pass-through
  fallback.
- `llm-provider-deepseek`: A standard-library HTTP client for the DeepSeek
  `deepseek-v4-pro` chat-completions API, including configuration via a `.env` file,
  request/response shaping, timeouts, and error handling.
- `humanize-cli`: The `--humanize` opt-in flag on `eqa questions` that routes
  generated items through the humanization stage and emits the reworded question and
  explanation alongside the unchanged answer fields.

### Modified Capabilities
<!-- No existing spec-level requirements change; humanization is additive and opt-in. -->

## Impact

- **Code**: `src/electronics_qa_generator/llm/` (new `humanize.py`, `provider.py`,
  `cache.py`); `src/electronics_qa_generator/questions/cli_handler.py` and `cli.py`
  (new `--humanize` flag + plumbing); `models.py` `QAItem` may gain an optional
  `explanation` consumer (field already exists).
- **APIs/External**: Adds an outbound dependency on the DeepSeek API
  (`deepseek-v4-pro`). Network calls only occur when `--humanize` is set and a key is
  configured; otherwise fully offline.
- **Dependencies**: No new required packages (stdlib `urllib` for HTTP, `json` for
  payloads). DeepSeek access configured via a `.env` file in the project root.
- **Invariant**: Strengthens rather than weakens the "LLM never creates truth" rule —
  the answer is computed before the LLM is called and re-verified after.
- **Tests/Reproducibility**: Default behavior unchanged; new tests use a fake/stub
  provider so no network access is required in CI.
