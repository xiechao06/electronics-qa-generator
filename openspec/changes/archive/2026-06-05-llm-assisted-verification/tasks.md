## 1. LLM check cache

- [x] 1.1 Add `LLMCheckCache` class to `validation/llm_checks.py` (or a separate
  cache module) modeled on `HumanizationCache`: JSON file cache keyed by
  `(check_name, question_text)`.

## 2. LLM check functions

- [x] 2.1 Add `src/electronics_qa_generator/validation/llm_checks.py` with three
  functions: `check_ambiguity(item, *, provider)`, `check_semantic_leakage(item, *,
  provider)`, `check_difficulty(item, *, provider)`. Each returns `CheckResult`.
- [x] 2.2 Implement `check_ambiguity`: system prompt asks "Is this question wording
  ambiguous or vague? Respond with PASS or WARN: <reason>." Parse response for
  PASS/WARN.
- [x] 2.3 Implement `check_semantic_leakage`: system prompt asks "Does this question
  implicitly reveal its own answer? Respond with PASS or WARN: <reason>." Include
  the stored answer as context so the LLM can detect leakage.
- [x] 2.4 Implement `check_difficulty`: system prompt asks "Rate this question's
  difficulty as easy, medium, or hard. Respond with the label only." Returns PASS
  verdict always, difficulty stored in message.
- [x] 2.5 Each check handles provider unavailability by returning PASS immediately
  (via `is_available()` check); catches `DeepSeekError` → PASS.
- [x] 2.6 Wire caching: before calling provider, check `LLMCheckCache`; after call,
  store result.

## 3. Integration with validation pipeline

- [x] 3.1 Register `LLM_CHECKS` list in `validation/checks.py` alongside
  `ITEM_CHECKS`.
- [x] 3.2 Update `ValidationReport.from_items()` to accept optional `provider` and
  `cache` keyword arguments; run LLM checks on each item when provider is
  available.
- [x] 3.3 Update `validation/cli_handler.py` (`run_validate`) to accept `--llm`
  flag and pass provider/cache to `from_items()`.
- [x] 3.4 Update `questions/cli_handler.py` to accept `--llm` alongside `--verify`.

## 4. CLI integration

- [x] 4.1 Add `--llm` flag to `eqa validate` subparser in `cli.py`.
- [x] 4.2 Add `--llm` flag to `eqa questions` subparser in `cli.py`.

## 5. Tests

- [x] 5.1 Add `tests/test_validation/test_llm_checks.py`: test each check with a
  fake provider (returns "PASS", "WARN: ambiguous", "easy"); test provider
  unavailability returns PASS; test cache hit/miss.
- [x] 5.2 Add CLI tests for `--llm` flag on validate and questions.

## 6. Docs and validation

- [x] 6.1 Run `uv run pytest`, `uv run ruff check .`, and `uv run ruff format .`;
  all must pass.
