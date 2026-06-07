---
name: enrich-from-problems
description: >
  Enrich the electronics QA generator with new question templates sourced from
  existing textbook/exam problems. Each problem must include a circuit image;
  solutions are optional. The skill guides an agent to: (1) extract a SPICE
  netlist from the image + problem text via VLM, (2) run Xyce simulation and
  extract facts, (3) synthesize a CLEVR-style program that retrieves each
  answer from the simulation result, (4) optionally compare against provided
  solutions, and (5) register the new template into the question set.
  Use when the user wants to add real exam/textbook problems to the dataset,
  "enrich from problems", "add new questions from images", or "import problems".
metadata:
  author: electronics-qa-generator
  version: "1.0"
---

# Enrich Question Templates from Existing Problems

Add new question templates — and optionally new circuit topologies — to the
pipeline from real textbook or exam problems. Every answer must still be
**simulation-derived**: the LLM is used only to interpret the circuit image and
describe the netlist; Xyce and deterministic code own all numerical truth.

**Core invariant (never violate):** The LLM never creates a numerical answer.
VLM → netlist extraction. Xyce → ground-truth facts. Program engine → answer.

All helper script paths below are relative to this skill directory
(`.pi/skills/enrich-from-problems/`). Run all CLI commands from the **repo
root** with `uv run`.

---

## Step 0 — Prepare input

Organise the problems to import into a directory:

```
problems/
├── problem_01/
│   ├── image.png          # circuit schematic (required)
│   ├── problem.md         # question text (required)
│   └── solution.md        # worked solution (optional)
├── problem_02/
│   ├── image.png
│   └── problem.md
...
```

- **image.png** — circuit schematic photograph or rendered image.
- **problem.md** — the problem statement. Include every question to be asked
  (one per line or numbered list). If there are multiple sub-questions (a, b, c)
  treat each as a separate question template entry.
- **solution.md** — optional. Include numerical answers, clearly labelled
  (e.g. `V(out) = 3.14 V`). Used in Step 5 for cross-checking.

Ask the user: "Where is your problems directory?" if not provided.

---

## Step 1 — Extract circuit topology and netlist (VLM)

For **each problem directory**, run the extraction script:

```bash
uv run python .pi/skills/enrich-from-problems/scripts/extract_netlist.py \
    <problem_dir> --out <problem_dir>/extracted.json
```

The script calls a local VLM (or the configured LLM provider) with the image
and problem text and asks it to output a structured JSON describing:
- `topology` — a kebab-case name (e.g. `rc_lowpass`, `bjt_ce_amplifier`)
- `family` — `passive` | `amplifier` | `filter` | `rectifier` | `resonance`
- `components` — list of `{ref, kind, pos, neg, value}` entries
- `directives` — SPICE analysis directives implied by the question
  (`.op` / `.dc` / `.ac` / `.tran`)
- `models` — any device models needed (e.g. BJT model card)

**Review the extracted JSON before proceeding.** Open it, check that:
- Component designators match what's drawn (R1, C1, Q1, …)
- Node names are meaningful (`in`, `out`, `base`, `collector`, …)
- Analysis directive matches what the question asks for
- All values are in SI base units (Ω, F, H, V, A)

Ask the user to confirm or correct before moving to Step 2. If the topology
already exists in `src/electronics_qa_generator/templates/`, note it and skip
topology registration in Step 6.

---

## Step 2 — Emit SPICE netlist

Run the netlist emitter on the extracted JSON:

```bash
uv run python .pi/skills/enrich-from-problems/scripts/emit_netlist.py \
    <problem_dir>/extracted.json --out <problem_dir>/circuit.sp
```

Open `circuit.sp` and verify it looks like valid SPICE. Key checks:
- Every component in the extracted JSON appears exactly once
- Analysis directive is present (`.op`, `.dc V1 …`, `.ac …`, `.tran …`)
- `.end` terminator is present
- Node `0` is ground

If anything looks wrong, go back to Step 1 and correct `extracted.json`.

---

## Step 3 — Run Xyce simulation and extract facts

Check Xyce is installed:

```bash
which Xyce
```

If not found, stop and tell the user:
> Xyce is not installed or not on your PATH. See https://xyce.sandia.gov/downloads/

Run simulation:

```bash
uv run python .pi/skills/enrich-from-problems/scripts/simulate_and_extract.py \
    <problem_dir>/circuit.sp \
    --topology <topology_name> \
    --out <problem_dir>/facts.json
```

Open `facts.json`. It is a flat dict of `fact_name → value` pairs (voltages,
currents, gains, frequencies, etc.). Every number in this dict is simulation
truth.

If the simulation **does not converge**, try:
1. Tweaking component values slightly in `extracted.json` (±10 %)
2. Re-emitting (Step 2) and re-simulating
3. If the topology itself is degenerate, discard this problem

---

## Step 4 — Synthesize CLEVR-style programs for each question

For each question in `problem.md`, create a program entry that:
1. **Reads** the relevant fact(s) from the simulation output using `read_fact`
2. **Formats** the answer using `format_numeric` or `classify`
3. **Never** computes a value — just retrieves and formats what Xyce produced

Use this reference for program ops (from `src/electronics_qa_generator/questions/programs.py`):

| Op | Purpose | Key args |
|---|---|---|
| `read_fact` | Look up a fact from the extracted dict | `fact` (key name) |
| `read_param` | Look up a circuit parameter | `param` |
| `format_numeric` | Format a number with unit + precision | `unit`, `precision`, `min_rel_tol` |
| `classify` | Map a numeric fact to a label | `thresholds`, `labels` |
| `compare` | Compare two values | `op` (`>`, `<`, `==`) |
| `boolean_label` | yes/no from a boolean fact | — |

Run the synthesis helper to get a starting template:

```bash
uv run python .pi/skills/enrich-from-problems/scripts/synthesize_program.py \
    <problem_dir>/facts.json \
    <problem_dir>/problem.md \
    --out <problem_dir>/question_templates.json
```

The script proposes a template for each question with:
- `id` — unique identifier (use `<topology>_<short_description>`)
- `question_type` — `direct` | `derived` | `classification` | `comparison`
- `question_template` — the question text with `{param}` placeholders
- `program` — the CLEVR-style program
- `answer_keys` — list of fact/param keys consumed by the program
- `answer_formatter` — `numeric` | `label` | `boolean`

**Review every proposed template.** Ensure:
- The `read_fact` key exactly matches a key in `facts.json`
- The `question_template` text refers only to what is visible in the schematic
- No numerical value is hard-coded — all values come via `{param}` placeholders
  or are read from the fact table

Manually correct anything that looks wrong before proceeding.

---

## Step 5 — Compare with provided solutions (optional)

If `solution.md` exists, run the verifier:

```bash
uv run python .pi/skills/enrich-from-problems/scripts/verify_solution.py \
    <problem_dir>/facts.json \
    <problem_dir>/solution.md \
    <problem_dir>/question_templates.json
```

The script extracts numerical values from `solution.md` (using regex patterns
like `= <number> <unit>`) and compares them against the simulation-derived
answers within tolerance.

Expected output for each question:
- `✓ MATCH` — simulation agrees with the solution within tolerance
- `✗ MISMATCH <sim_value> vs <solution_value>` — investigate:
  - Wrong component value in `extracted.json`? Fix and re-simulate.
  - Solution uses an approximation? Record it; simulation truth wins.
  - Solution is wrong? Document in `problem_dir/notes.md`.

**Simulation truth always wins.** A mismatch means either the netlist is wrong
or the solution is approximate/incorrect. Never adjust the simulation output to
match the solution.

---

## Step 6 — Register into the question set

### 6a. If the topology already exists

Append the new templates to the appropriate entry in
`src/electronics_qa_generator/questions/templates.py`:

```python
QUESTION_TEMPLATES["<topology>"] = [
    *QUESTION_TEMPLATES.get("<topology>", []),
    # --- new templates from <problem_dir> ---
    {
        "id": "...",
        "question_type": "...",
        ...
    },
]
```

Also add any new fact keys used by the programs to the `FACT_INPUTS` table in
`src/electronics_qa_generator/validation/template_coverage.py`.

### 6b. If the topology is new

1. Create a new `CircuitTemplate` subclass in
   `src/electronics_qa_generator/templates/<topology>.py` following the pattern
   in `src/electronics_qa_generator/templates/passive.py`. The `sample(seed)`
   method must produce the same component values as `extracted.json` at seed 0
   (use the extracted values as defaults; add ±20 % random sampling around them
   for diversity).
2. Register the template in `src/electronics_qa_generator/templates/__init__.py`.
3. Create an SVG schematic template in
   `src/electronics_qa_generator/render/svg/<topology>.svg` mirroring the
   circuit image, with value slots (`id="slot-R1"`, etc.) and node labels.
4. Register the SVG in `src/electronics_qa_generator/render/svg_templates.py`.
5. Add the question templates to `QUESTION_TEMPLATES` as in 6a.
6. Add a `FACT_INPUTS` entry in `validation/template_coverage.py`.
7. Run the coverage verifier:
   ```bash
   uv run eqa verify-templates
   ```
8. Run the tests:
   ```bash
   uv run pytest --ignore=tests/test_llm
   ```

---

## Step 7 — Verify end-to-end

Test that the new question(s) generate correctly:

```bash
uv run eqa emit <topology> --seed 0 -o /tmp/test_enrich --render
uv run eqa simulate <topology> --seed 0
uv run eqa questions <topology> --seed 0 -o /tmp/test_enrich
```

Inspect the generated QA items:
```bash
cat /tmp/test_enrich/qa_items.jsonl | python3 -m json.tool | head -60
```

Check:
- `question` text is natural and unambiguous
- `answer` is non-trivial (not zero, not degenerate)
- `schematic_path` points to a valid PNG
- `program` steps all resolve without `KeyError`

If anything fails, trace back through the steps.

---

## Step 8 — Update README counts

After adding templates or a new topology, the README.md topology count and
QA-per-seed count must reflect the new totals. Run:

```bash
uv run python .pi/skills/enrich-from-problems/scripts/update_readme_counts.py
```

This automatically updates:
- `## Available topologies (N)` heading
- The topology grid inside the code block
- `--topologies | all N |` table row
- `N circuit topologies` in the pipeline diagram label

Review the diff (`git diff README.md`) to confirm it looks right before committing.

---

## Step 9 — Commit

Once all questions pass and README is updated, commit the changes:

```bash
git add -A
git commit -m "Add question templates from <source> problems"
git push origin main
```

---

## Quick reference: fact naming conventions

| Quantity | Fact key pattern | Unit |
|---|---|---|
| DC node voltage | `V<node>_dc` | V |
| AC voltage magnitude | `V<node>_mag_V` | V |
| AC voltage phase | `V<node>_phase_deg` | ° |
| DC current | `I<comp>_dc` | A or mA |
| Power | `P<comp>_mW` | mW |
| Gain (magnitude) | `gain_db` or `gain_lin` | dB or — |
| Cutoff frequency | `cutoff_hz` | Hz |
| Resonant frequency | `resonant_hz` | Hz |
| Rise time | `rise_time_us` | µs |

When a needed fact key doesn't exist yet, add it to the relevant extractor in
`src/electronics_qa_generator/extraction/facts.py`.
