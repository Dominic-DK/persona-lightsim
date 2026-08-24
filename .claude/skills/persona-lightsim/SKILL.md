---
name: persona-lightsim
description: Lightweight persona simulation with no node-to-node dialogue — batch judgment (one agent call judges 25 personas) → deterministic aggregation → opinion re-injection second pass (mean-field) → segment representative card distillation → local pack (sqlite) loading. Use this skill for "lightweight simulation", "simulate without dialogue", "judge persona reactions/receptivity", "make persona cards", "load into a pack", "query the pack", and follow-ups ("redo just the second pass", "re-distill cards", "rebuild the pack", "refresh judgments with a different brief"). Questions needing real-time agent-interaction simulation (diffusion/intervention dynamics) are out of scope — that is an OASIS-style multi-agent simulation track.
---

# Lightweight Persona Simulation (persona-lightsim)

**Execution mode: subagents** (batch judgment and distillation are independent fan-outs — no team communication needed. Aggregation and loading are deterministic scripts).

Two core ideas:
1. **The unit of an LLM call is a batch.** Not one call per persona: one `persona-batch-judge` call judges 25 personas — a 100-persona sample is 4 calls per pass.
2. **Interaction is a mean-field approximation.** Instead of making nodes talk, aggregate the first-pass judgments deterministically and re-inject the result as an "opinion summary" in a second pass. First-order social effects (conformity, hardening) are captured; structural effects (echo chambers) are given up — that belongs to the interaction-simulation track.

## Pipeline

Workspace: `_workspace/persona-lightsim/` (or a per-run directory). Artifact contract:

```
brief.md                      # product facts brief (persona-brief-auditor audit required)
personas/{country}.jsonl      # sample (persona-research sampler)
slices/batch{i}.jsonl         # 25-persona slices (with idx field)
judgments/pass1_batch{i}.jsonl
aggregate/pass1_aggregate.json / pass1_opinion_summary.md
judgments/pass2_batch{i}.jsonl
aggregate/pass2_aggregate.json
cards.json                    # distilled persona cards
persona_pack.sqlite3 (+ _nodes.json)
```

### Step 1: Sample + slice
Sample with the `persona-research` skill's sampler, then split into 25-persona slices, assigning `idx` to each row. idx is the join key for judgments and evidence quotes.

```bash
# The sampler needs pyarrow — always run through the dedicated venv (bare python3 → ModuleNotFoundError)
data/.venv-personas/bin/python .claude/skills/persona-research/scripts/sample_personas.py \
  --countries korea --n 100 --seed <seed> --out <run dir>/personas
# Without a venv: uv run --with pyarrow python3 <same args>
# No data at all yet? First: python3 scripts/setup_data.py
```

Slicing reads the sample JSONL in line order, cuts every 25 rows, and writes `slices/batch{i}.jsonl` with `idx` (global running number from 0) added to each row. The original sample file has no idx — line order IS idx.

### Step 2: Batch judgment (pass 1)
Spawn one `persona-batch-judge` agent per slice, concurrently. Judgment schema:

```json
{"idx": int, "adoption": "yes|maybe|no", "payment": "lifetime|monthly|free_ads|none",
 "reason": "one sentence quoting concrete elements of the persona text", "objection": "one sentence or null", "segment": "short label"}
```

Discipline: no assuming features beyond the brief; if no then payment=none; a majority of indifference is realistic (no forced yes); no missing persons.

### Step 3: Aggregation (deterministic, 0 LLM calls)
```bash
python3 .claude/skills/persona-lightsim/scripts/aggregate_judgments.py \
  --judgments <judgments dir> --pass-name pass1 --out <aggregate dir> --expected-n <sample size>
```
Doubles as the schema-validity ≥95% gate (on FAIL, rerun the offending batch). Among the outputs, `pass1_opinion_summary.md` is the re-injection payload.

### Step 4: Opinion re-injection (pass 2)
Re-judge the same slices with `pass1_opinion_summary.md` added. The pass-2 schema is pass 1 + `"opinion_shift": "none|softened|hardened"` + `"shift_reason"` (when shifted). Validation: the shift rate must be neither 0% nor 100% — 0% signals the summary was ignored, 100% signals over-conformity.

### Step 5: Distillation
One `persona-distiller` agent reads the 2-pass judgments + the original sample and builds segment representative cards. **Immutable/variable separation** is the heart of the schema:

```json
{"cards": [{"card_id": "kr-learning-aspiration-midlife", "segment": "...", "size_pct": 13.0, "country": "korea",
  "immutable": {"label": "...", "demographics": "...", "narrative": "..."},
  "evidence": [{"persona_idx": 12, "quote": "verbatim quote", "field": "persona"}],
  "judgment": {"adoption": "...", "payment": "...", "key_reason": "...", "key_objection": "...", "opinion_shift": "..."}}]}
```

Immutable (immutable/evidence) is demographics and narrative — reusable regardless of product. Variable (judgment) is bound to this brief — when the product changes, rerun only steps 2–5 to refresh judgments.

### Step 6: Pack loading + queries
```bash
python3 .claude/skills/persona-lightsim/scripts/build_opencrab_pack.py build \
  --cards cards.json --brief brief.md --brief-id <product-slug> --pack persona_pack.sqlite3
python3 ...build_opencrab_pack.py query --pack ... --q payment_segments   # 3 verification queries
```
Node grammar is the space/node_type/node_id/properties graph-pack format — it produces both sqlite and a `_nodes.json` export, so it can be imported into an external knowledge-graph system. Whether to import is a manual decision outside this pipeline.

## Error handling

| Situation | Handling |
|---|---|
| Batch judgment validity <95% | Respawn only that batch once; on second failure, proceed without it (note the gap in aggregation) |
| Pass-2 shift rate 0% or 100% | Check the re-injection prompt, rerun that pass once; if it repeats, note the warning in results |
| Card with <2 evidence quotes | Ask the distiller to reinforce only the deficient cards |
| Empty pack query results | Check cards.json ↔ pack schema consistency (rerun build) |

## Test scenarios

1. **Happy path**: "Run a 100-persona Korea light sim on brief X and build a pack" → steps 1–6, all 3 pack queries pass (original-harness measurements: 99/99 valid, 24.2% pass-2 shift rate, 8 cards with 39/39 evidence quotes verified verbatim)
2. **Judgment refresh**: "The brief changed — refresh judgments only" → reuse existing samples and card immutables, rerun steps 2–5, then `build` updates only the Judgment nodes
3. **Error**: batch2 validity 80% → respawn batch2 only → after passing, rerun aggregation
