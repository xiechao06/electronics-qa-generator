## 1. DeepSeek provider client

- [x] 1.1 Add `src/electronics_qa_generator/llm/provider.py` with a `DeepSeekError`
  exception and a `DeepSeekClient` (or `complete()` function) that POSTs to the
  chat-completions endpoint using only `urllib.request` + `json`.
- [x] 1.2 Read config from a `.env` file in the project root (stdlib key-value
  parser, no `python-dotenv` dependency): `DEEPSEEK_API_KEY` (required),
  `DEEPSEEK_BASE_URL` (default DeepSeek endpoint), `DEEPSEEK_MODEL` (default
  `deepseek-v4-pro`); expose an `is_available()` check based on key presence.
- [x] 1.3 Apply a bounded request timeout; map network errors, non-2xx responses, and
  malformed JSON to `DeepSeekError`.
- [x] 1.4 Add unit tests with a monkeypatched `urllib` (no network): success returns
  content; missing key reports unavailable; timeout/non-2xx/bad-JSON raise
  `DeepSeekError`; assert no third-party HTTP import is used.

## 2. Humanization cache

- [x] 2.1 Add `src/electronics_qa_generator/llm/cache.py` mirroring
  `simulation/cache.py`: JSON file cache keyed by a hash of
  `(original_question, model, options_signature)`.
- [x] 2.2 Add tests for cache put/get round-trip and key sensitivity to model/options.

## 3. Humanization stage

- [x] 3.1 Add `src/electronics_qa_generator/llm/humanize.py` with `humanize_item(item,
  *, provider=None, cache=None, explain=True)` that copies all deterministic fields
  from the input `QAItem` and only updates `question`/`explanation`.
- [x] 3.2 Define the prompt contract (system + user messages) instructing the model to
  preserve all quantities/units/numbers and reword phrasing only; parse the response
  into reworded `question` and optional `explanation`.
- [x] 3.3 Implement the answer-preservation guard: reject rewordings that drop/alter the
  unit token or numeric answer string present in the original, keeping the original
  question on rejection; never source answer fields from the model.
- [x] 3.4 Implement offline-safe pass-through: when the provider is unavailable or
  raises `DeepSeekError` (or output is malformed), return the input item unchanged.
- [x] 3.5 Wire caching: check cache before calling the provider; store result after.
- [x] 3.6 Add tests with a fake provider: reword preserves all answer fields; explanation
  attaches when enabled; answer-drift output is rejected; no-key pass-through; cache hit
  avoids a second provider call.

## 4. CLI integration

- [x] 4.1 Add a `--humanize` flag to the `questions` subparser in `cli.py`.
- [x] 4.2 In `questions/cli_handler.py`, when `--humanize` is set, map each generated
  item through `humanize_item`; add `explanation` to the emitted JSON/JSONL object.
- [x] 4.3 Ensure the stage is best-effort: provider failure/unavailability emits original
  items and exits 0; default (no flag) path makes no provider call and is unchanged.
- [x] 4.4 Add tests: `--humanize` with a fake provider emits reworded question +
  explanation while answer fields match the non-humanized output; without the flag,
  output is byte-identical to current behavior.

## 5. Docs and validation

- [x] 5.1 Document `.env` file setup (`DEEPSEEK_API_KEY`, and optional
  `DEEPSEEK_BASE_URL`/`DEEPSEEK_MODEL`) plus the `--humanize` flag in `README.md`;
  ensure `.env` is in `.gitignore`.
- [x] 5.2 Run `uv run pytest`, `uv run ruff check .`, and `uv run ruff format .`; ensure
  all pass and formatting is clean before marking the change ready to archive.
