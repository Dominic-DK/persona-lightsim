# persona-lightsim

**English** | [한국어](README.ko.md) | [日本語](README.ja.md) | [中文](README.zh.md)

A lightweight persona market-research & simulation harness for [Claude Code](https://claude.com/claude-code). It maps any product onto **synthetic populations of 10 countries** (NVIDIA [Nemotron-Personas](https://huggingface.co/nvidia)) and produces use-case analyses, willingness-to-pay readings, batch-judged reaction simulations, and reusable persona cards — with **no web app, no simulation server, and a 63MB dataset**.

## Have your AI set it up

Paste this to Claude Code (or any coding agent):

```
Set up https://github.com/Dongkyu-ES/persona-lightsim for me:
1. git clone https://github.com/Dongkyu-ES/persona-lightsim && cd persona-lightsim
2. python3 scripts/setup_data.py        # downloads the 63MB lite dataset from HuggingFace + creates the pyarrow venv
3. Run the smoke test command that setup prints, and show me the result.
Korean skill docs: python3 scripts/set_language.py ko (default is English).
```

That's it. Open the repo in Claude Code and ask things like:

- *"Map product X onto the 10-country personas and analyze use cases and willingness to pay"* → `persona-research` skill (parallel per-country analyst fan-out)
- *"Run a lightweight simulation of 100 Korean personas reacting to this brief, then build a pack"* → `persona-lightsim` skill (batch judgment → mean-field 2-pass → card distillation → sqlite pack)

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

`scripts/setup_data.py` fetches the **lite pack** — [`__HF_DATASET_ID__`](https://huggingface.co/datasets/__HF_DATASET_ID__) — a derived redistribution of NVIDIA's Nemotron-Personas datasets (CC-BY-4.0):

- 10 countries: Belgium, Brazil, El Salvador, France, India, Japan, Korea, Singapore, USA, Vietnam
- 10,000 personas per country, seed-42 subsample of the 0.1M–1.2M originals
- 15 of 26 columns (the ones this harness reads), long narrative fields trimmed to 300–400 chars
- Original shard structure preserved (Belgium language quotas, India English-only) — the sampler runs unchanged on lite or full data
- **~63MB total** vs ~24GB for the originals

Need the full, untrimmed data? Download the NVIDIA originals from HuggingFace and point the env var at them:

```bash
export NEMOTRON_PERSONAS_BASE=/path/to/full-data   # parent dir of nemotron-personas-*/
```

## Notes and limits

- Personas are synthetic population composition, not behavioral logs. Every skill enforces writing conclusions as **directional hypotheses** to validate with experiments.
- The lightweight simulation is a **mean-field approximation**: first-order social effects (conformity/hardening) are captured; structural effects (echo chambers, diffusion dynamics) are out of scope.
- Agent definitions default to `model: opus`; edit `.claude/agents/*.md` to change.

## License

Code: [MIT](LICENSE). Lite dataset: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/), derived from NVIDIA Nemotron-Personas (© NVIDIA, CC-BY-4.0) — see the dataset card for attribution details.
