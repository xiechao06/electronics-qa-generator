## ADDED Requirements

### Requirement: Assemble command runs full pipeline

The `eqa assemble` command SHALL run the full pipeline for all 5 topologies (sample →
simulate → extract → generate → verify → assemble) and produce a complete dataset in
the output directory.

#### Scenario: Default run produces dataset

- **WHEN** `eqa assemble --out my_dataset` runs
- **THEN** 25 items are written to `my_dataset/dataset.jsonl` with 5 schematic PNGs
  under `my_dataset/images/`

#### Scenario: Consistent seed across topologies

- **WHEN** `eqa assemble --seed 42` runs
- **THEN** each topology uses the same seed for reproducibility

### Requirement: Assemble subcommand flags

The command SHALL accept `--out` (output directory, default `dataset/`), `--seed`
(default 0), and `--cache-dir` / `--no-cache` for simulation caching.

#### Scenario: Custom output directory

- **WHEN** `eqa assemble --out benchmarks/v1` runs
- **THEN** output is written under `benchmarks/v1/`
