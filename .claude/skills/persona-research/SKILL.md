---
name: persona-research
description: Orchestrator for market and use-case analysis of any product/service against the Nemotron-Personas 10-country dataset (data/nemotron-personas-*). Use this skill whenever the user asks for persona analysis, "sample N personas and derive use cases", "map product X onto users in each country", "willingness to pay by market", "quantify target segments", or follow-ups ("rerun", "redo Korea only", "update with a new brief", "add a country"). This is a lightweight track that runs on agent fan-out alone — no web app or simulation infrastructure required.
---

# Persona Research Orchestrator

**Execution mode: hybrid** — sampling & brief (deterministic script + subagent) → country analysis (parallel subagent fan-out; cross-country analyses are deliberately blind and independent, so no inter-agent communication is needed) → synthesis (lead) → verification (QA subagent). Run agent calls on the strongest model available.

## Data flow

File-based + return-value-based. Workspace: `_workspace/persona-research/`

```
_workspace/persona-research/
├── brief.md                  # product reality brief (audited)
├── personas/{country}.jsonl  # samples
├── reports/{country}.md      # country reports (lead saves analyst return values)
└── critic.md                 # QA findings
```

Only the final deliverable goes to `docs/research/persona-{product}-{YYYY-MM}.md`. Keep `_workspace/` as the audit trail.

## Phase 0: Context check

1. Check whether `_workspace/persona-research/` exists:
   - Exists + partial-change request ("redo Korea only", "refresh the brief") → **partial rerun**: re-invoke only the affected stage's agents, reuse everything else
   - Exists + new product / new sample request → move the old workspace to `_workspace/persona-research_prev/`, then **fresh run**
   - Missing → **initial run**
2. Confirm the target product — get the repo/docs path for the brief from the user's request. If absent, ask this one question only.
3. Confirm the analysis axis — default is "use cases + willingness to pay". If the request is a specific question (feature priority, pricing experiment, positioning), state that axis in the analyst prompts.

## Phase 1: Brief (generate-then-verify pattern)

1. The lead drafts the brief from the product repo/docs — features / pricing / known real-world weaknesses, 1–2 pages
2. Audit with the `persona-brief-auditor` agent — sentences without code-level evidence are removed or marked "assumption"
3. Save the audited brief to `_workspace/persona-research/brief.md`

Brief quality is the ceiling on the whole analysis. Do not skip this phase.

## Phase 2: Sampling (deterministic)

```bash
data/.venv-personas/bin/python .claude/skills/persona-research/scripts/sample_personas.py \
  --n 1000 --seed 42 --out _workspace/persona-research/personas [--countries korea,japan,...]
```

- If the data is missing, first run: `python3 scripts/setup_data.py` (downloads the lite pack and sets up the venv)
- If the venv is missing: `python3 -m venv data/.venv-personas && data/.venv-personas/bin/pip install pyarrow` (or ad hoc: `uv run --with pyarrow python3 ...`)
- Running with bare `python3` dies on missing pyarrow — the script exits with both alternatives printed.
- Samples are reproducible unless you change the seed. On reruns, reusing existing samples is the default.
- At small N (<100), rounding allocation can leave a country a few personas short (normal). At N=1000 expect 996–1000.
- Data location defaults to `data/`; override with the `NEMOTRON_PERSONAS_BASE` env var (works with both the lite pack and the full data).

## Phase 3: Country analysis fan-out

Spawn one `persona-country-analyst` per country, **all in a single message**. Each prompt includes:
- Follow the agent definition (`.claude/agents/persona-country-analyst.md`) and the `persona-country-analysis` skill
- Two inputs: `brief.md` + `personas/{country}.jsonl` (absolute paths)
- The analysis axis (fixed in Phase 0)
- Return: the 7-section report text

The lead saves each return value to `reports/{country}.md`.

## Phase 4: Cross-market synthesis (lead)

Read all 10 reports closely, then:
1. **3–5 cross-market findings** — patterns recurring across countries; state the number of supporting countries for each
2. **Action implications** — for marketing / product / pricing, each at immediately actionable level
3. Preserve every country report verbatim as an appendix
4. State data source, sampling method, and limitations ("directional hypotheses, validate with experiments") at the top of the document

## Phase 5: Verification (QA)

Hand the synthesis draft + country reports + sample paths to the `persona-synthesis-critic` agent for adversarial recheck. Apply REFUTED findings; note unresolved items as limitations. After passing, save the final document to `docs/research/` and report a summary to the user.

## Phase 6 (optional): Lightweight simulation → card distillation → pack loading

If the request goes beyond analysis — "judge personas' reactions to the product", "opinion re-injection 2-pass", "distill segment cards", "load a local pack" — continue with the `persona-lightsim` skill. That track consumes this skill's sample and brief artifacts directly (agents: `persona-batch-judge`, `persona-distiller`).

## Error handling

| Situation | Handling |
|---|---|
| One country analyst fails | Retry once → on second failure, proceed without that country and note the omission in the synthesis |
| Sample file missing | Rerun Phase 2 (samples are always regenerable) |
| Request for a country not on disk | Suggest `python3 scripts/setup_data.py --countries <country>`, confirm with the user |
| Brief cannot be audited (no repo access) | Stop and ask the user to confirm product facts — never fan out with an unaudited brief |
| Critic vs analyst verdict conflict | Keep both positions side by side with sources; do not delete |

## Test scenarios

1. **Happy path**: "Map product X onto 10-country personas and analyze use cases" → Phases 0–5, producing `docs/research/persona-X-YYYY-MM.md`
2. **Partial rerun**: "Redo only the Korea report from a learning-tool angle" → Phase 0 detects partial rerun → respawn only the Korea analyst → update only Korea-related sentences in the synthesis → partial critic recheck
3. **Error path**: Brazil analyst fails twice → synthesize from 9 countries, note "Brazil omitted" up front

## Cost/time expectations

Measured (original harness): a full 10-country parallel analysis fits in one session, ~30 minutes. No extra infrastructure — this skill uses only the data directory and agents.
