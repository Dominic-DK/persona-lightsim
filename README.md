# persona-lightsim

**English** | [한국어](README.ko.md) | [日本語](README.ja.md) | [中文](README.zh.md)

A lightweight persona market-research & simulation harness for [Claude Code](https://claude.com/claude-code). It maps any product onto **synthetic populations of 10 countries** (NVIDIA [Nemotron-Personas](https://huggingface.co/nvidia)) and produces use-case analyses, willingness-to-pay readings, batch-judged reaction simulations, and reusable persona cards — with **no web app, no simulation server, and a 63MB dataset**.

## Have your AI set it up

Paste this to Claude Code (or any coding agent):

```
Set up https://github.com/Dominic-DK/persona-lightsim for me:
1. git clone https://github.com/Dominic-DK/persona-lightsim && cd persona-lightsim
2. python3 scripts/setup_data.py        # downloads the 63MB lite dataset from HuggingFace + creates the pyarrow venv
3. Run the smoke test command that setup prints, and show me the result.
Korean skill docs: python3 scripts/set_language.py ko (default is English).
```

That's it. Open the repo in Claude Code and ask things like:

- *"Map product X onto the 10-country personas and analyze use cases and willingness to pay"* → `persona-research` skill (parallel per-country analyst fan-out)
- *"Run a lightweight simulation of 100 Korean personas reacting to this brief, then build a pack"* → `persona-lightsim` skill (batch judgment → mean-field 2-pass → card distillation → sqlite pack)

## How to use it

Open the repo in Claude Code and describe the run in one sentence. A request has four slots:

> **{product — and where its code or docs live}** → **{which countries}** → **{how many personas each}** → **{the question you actually have}**

Only the product is required. Countries default to all 10, sample size to n=1000 per country, and the analysis axis to "use cases + willingness to pay". Whatever you leave out is either defaulted or asked about once.

### Whole-market scan

The run that produced [`examples/quest15/`](examples/quest15/):

```
Projects/Quest15 is a location-based iOS app that hands you one 10-15 minute
micro-adventure wherever you're standing. Read the repo, build the product
brief from the actual code, then map it onto all 10 countries at n=1000 and
analyze use cases and willingness to pay.
```

The harness drafts a brief from the codebase, has `persona-brief-auditor` strip every claim with no code-level evidence, samples ~1,000 personas per country, fans out 10 country analysts in parallel (blind to each other), synthesizes across markets, then hands the draft to an adversarial critic before writing the final document. Roughly 30 minutes end to end.

### Narrow the countries, sharpen the question

```
Run the TripRoll brief against Korea, Japan, and Vietnam only, 1000 each.
Skip general use cases - I need to know whether a one-off 9,900 KRW per-trip
charge reads better than a monthly subscription in each of the three markets.
```

Naming an axis changes what every analyst looks for. Axes that work well: pricing-structure comparison, feature priority, positioning and messaging, churn risk, or the real size of one segment.

### Focus on a segment

```
Same TripRoll brief, Korea + Singapore, n=1000. Focus on people who travel in
groups - friends, couples, extended family. Quantify how large that segment
actually is in each sample before drawing any conclusion from it.
```

### Lightweight simulation and a reusable pack

```
Take the audited Quest15 brief and run a light sim on 100 Korean personas:
batch judgment, opinion re-injection second pass, distill segment cards, and
build the sqlite pack. Show me the adoption and payment split for both passes.
```

100 personas is 4 agent calls per pass (one call judges 25), so 8 calls plus a deterministic aggregation step in between. You get per-persona adoption/payment/objection judgments, a first-pass opinion summary re-injected into a second pass, segment cards carrying verbatim evidence quotes, and a queryable sqlite pack.

### No repo yet

```
There's no code - this is still an idea. [3-4 sentences of concrete facts:
what it does, who it's for, what you would charge.] Build the brief from that,
mark everything you can't verify as an assumption, then run France and Belgium
at n=1000 for use cases and pricing.
```

The auditor has nothing to check claims against here, so it labels them assumptions and the analysts treat them as such. The brief is the ceiling on the entire analysis - vague in, vague out.

### Follow-ups

Both skills detect an existing `_workspace/` and rerun only what changed:

- *"Redo only the Korea report, this time from a solo-traveler angle."*
- *"Add India to the existing run."*
- *"The brief changed - pricing is free-with-ads now. Refresh the judgments only; keep the samples and the card immutables."*
- *"Re-distill the cards, at least 3 evidence quotes each."*
- *"Query the pack for payment segments."* — the pack answers `payment_segments`, `top_objections`, and `card_evidence --card <card_id>`

### How conditions are actually applied

The sampler takes only `--countries`, `--n`, and `--seed` — there is no demographic filter. A condition like "women in their 30s" or "people who travel in groups" is therefore applied **downstream**: as keyword-and-demographic screening inside the analysis, with the report stating that segment's real count within a representative sample. That is usually what you want — a share of the population, not a share of a pre-filtered pool.

If you do want a hard filter, ask for it explicitly ("keep only personas aged 30-39, then analyze") and the agent post-filters the sample JSONL. Percentages in that report are then shares of the filtered pool and are no longer comparable with a full-sample run.

### What lands on disk

| Path | What |
|---|---|
| `_workspace/persona-research/` | brief, per-country samples, per-country reports, critic findings — the audit trail |
| `docs/research/persona-{product}-{YYYY-MM}.md` | the final cross-market document |
| `_workspace/persona-lightsim/` | slices, both passes of judgments, aggregates, `cards.json` |
| `_workspace/persona-lightsim/persona_pack.sqlite3` | the queryable pack (+ a `_nodes.json` export) |

Samples are reproducible from the seed, so reruns reuse them by default instead of redrawing.

## What's inside

| Piece | Role |
|---|---|
| `.claude/skills/persona-research` | Orchestrator: brief audit → sampling → per-country analyst fan-out → synthesis → QA |
| `.claude/skills/persona-country-analysis` | Unit methodology: real-count screening → close reading → 7-section report |
| `.claude/skills/persona-lightsim` | Dialogue-free simulation: batch judgment (1 call = 25 personas) → deterministic aggregation → opinion re-injection 2nd pass → segment cards → local pack |
| `.claude/agents/persona-*` (5) | brief-auditor / country-analyst / synthesis-critic / batch-judge / distiller |
| `scripts/setup_data.py` | Downloads the lite dataset (sha256-pinned manifest) and sets up the venv |
| `scripts/set_language.py` | Switches active skill/agent docs between `en` and `ko` |

Design principles carried over from the original harness, where this pipeline was measured end-to-end: 99/99 schema-valid batch judgments, a 24.2% opinion-shift rate on the second pass (neither 0% nor 100% — the mean-field re-injection demonstrably works), and 39/39 card evidence quotes verified verbatim against the sample.

## The data

`scripts/setup_data.py` fetches the **lite pack** — [`dominicDK94/nemotron-personas-lite`](https://huggingface.co/datasets/dominicDK94/nemotron-personas-lite) — a derived redistribution of NVIDIA's Nemotron-Personas datasets (CC-BY-4.0):

- 10 countries: Belgium, Brazil, El Salvador, France, India, Japan, Korea, Singapore, USA, Vietnam
- 10,000 personas per country, seed-42 subsample of the 0.1M–1.2M originals
- 15 of 26 columns (the ones this harness reads), long narrative fields trimmed to 300–400 chars
- Original shard structure preserved (Belgium language quotas, India English-only) — the sampler runs unchanged on lite or full data
- **~63MB total** vs ~24GB for the originals

Need the full, untrimmed data? Download the NVIDIA originals from HuggingFace and point the env var at them:

```bash
export NEMOTRON_PERSONAS_BASE=/path/to/full-data   # parent dir of nemotron-personas-*/
```

## Example outputs

Real, unedited research runs made with this harness — audited brief, 10 country reports,
cross-country synthesis, and the adversarial critic verdict for each:

- [`examples/quest15/`](examples/quest15/) — location-based micro-quest iOS app
- [`examples/triproll/`](examples/triproll/) — shared travel film-roll iOS app
- [`examples/sample-personas.md`](examples/sample-personas.md) — the exact n=1,000/country samples used (seed 42)

## Notes and limits

- Personas are synthetic population composition, not behavioral logs. Every skill enforces writing conclusions as **directional hypotheses** to validate with experiments.
- The lightweight simulation is a **mean-field approximation**: first-order social effects (conformity/hardening) are captured; structural effects (echo chambers, diffusion dynamics) are out of scope.
- Agent definitions default to `model: opus`; edit `.claude/agents/*.md` to change.

## License

Code: [MIT](LICENSE). Lite dataset: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/), derived from NVIDIA Nemotron-Personas (© NVIDIA, CC-BY-4.0) — see the dataset card for attribution details.
