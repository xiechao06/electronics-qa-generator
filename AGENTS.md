# AGENTS.md

Guidance for AI coding agents working in this repository.

## What this project is

A pipeline that generates **multimodal electronics circuit Q/A items** with
**SPICE/Xyce-grounded ground-truth answers**, for an MMMU-style benchmark.
Inspired by **CLEVR** (questions backed by executable programs) and **AutoCkt**
(simulator-in-the-loop as the source of truth).

Read these before doing design work:

- `docs/plan.md` — the full plan (circuit families, sims, question taxonomy, MVP)
- `docs/architecture.md` — end-to-end architecture and data flow
- `docs/circuit_qa_program_language.md` — CLEVR-style DSL for QA programs
- `docs/clevr_explained.md`, `docs/autockt_explained.md`, `docs/papers.md` — background

## The non-negotiable invariant

> **The LLM never creates truth. Simulation establishes facts, code derives
> answers, and the LLM only paraphrases/explains/tags after the answer is fixed.**

When implementing question or answer logic:

- Compute every numeric answer from simulation output or deterministic code.
- Never ask an LLM for a value, a behavior label, or a correct option.
- Every QA item should carry a machine-readable program (CLEVR-style) and a
  traceable link back to a fact in the extracted fact table.

## Tooling

- **Build/env:** `uv` only. Do not use `pip`/`poetry`/`conda`.
- **Python:** pinned to **3.14** via `.python-version`. Do not change without asking.
- Common commands:
  - `uv sync` — install (dev tools included)
  - `uv run eqa ...` — run the CLI
  - `uv run pytest` — tests
  - `uv run ruff check .` and `uv run ruff format .` — lint/format
- Add runtime deps with `uv add <pkg>`; dev deps with `uv add --dev <pkg>`.
  Prefer the existing optional-dependency extras (`sim`, `data`, `render`) for
  stage-specific heavy deps rather than adding them to base `dependencies`.

## Code organization

One subpackage per pipeline stage under `src/electronics_qa_generator/`:

```
templates → sampling → netlist → simulation → parsing → extraction
  → questions → llm → validation → rendering → output
```

- Shared data structures live in `models.py` (`CircuitRecord`, `QAItem`,
  `Sample`). Extend these rather than inventing parallel record shapes.
- End-to-end flow lives in `pipeline.py`. Keep stages decoupled and testable in
  isolation.
- The CLI lives in `cli.py` (the `eqa` console script). Wire new capabilities in
  as subcommands.

## Conventions

- Target Python 3.14; use modern typing (`X | None`, builtin generics, no
  `from __future__` needed except where already present for consistency).
- Keep functions deterministic where they touch ground truth; isolate randomness
  in `sampling/` behind explicit seeds for reproducibility.
- Every accepted sample must be **reproducible from stored metadata** (seed +
  template + parameters), per the architecture doc.
- Add a focused test under `tests/` for each stage you implement.

## Working style

- This is an MVP being built **step by step**. Implement one stage at a time; do
  not scaffold large speculative subsystems.
- Start from the MVP scope in `docs/plan.md` §9 (5 families, `.op/.dc/.ac/.tran`,
  4 question types) before expanding.
- Keep `mmmu_electronics*/` reference data read-only; treat it as the target
  schema, not something to modify.
- Run `uv run pytest` and `uv run ruff check .` before declaring work done.
