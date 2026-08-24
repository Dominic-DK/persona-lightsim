---
name: persona-country-analysis
description: Methodology for analyzing one country's Nemotron-Personas sample (~1,000-person JSONL) via quantitative screening + qualitative close reading into a 7-section structured report. When a persona-country-analyst agent is assigned a country analysis, it must follow this skill. The unit methodology for "persona analysis", "use-case derivation", and "segment quantification" work.
---

# Country-Level Persona Analysis Methodology

A procedure validated on a 10-country analysis with the original harness. The core is three stages — **real counts → close reading → structured output** — and no stage may be skipped.

## Stage 1: Quantitative screening

Write the screening script with the python3 standard library only (json, re, collections). No pandas needed — the sample is ~2MB of JSONL.

**Text fields**: concatenate `persona`, `professional_persona`, `arts_persona`, `hobbies_and_interests_list`, `skills_and_expertise_list`, `career_goals_and_ambitions` into one blob for matching. Demographics come from `sex/age/education_level/occupation/province`.

**Keyword dictionary design principles**:
- Always design directly in that country's idiomatic language. Not translations of English keywords, but the words that culture actually uses (Korean '자격증'·'인강', Japanese '資格取得'·'買い切り', French 'club de lecture'·'VO').
- Anchor segments to the product brief's features and pricing — not "hobby taxonomy" but "reasons this person would or wouldn't use this product".
- Count at persona granularity (multiple hits from the same person count once).

**False-positive verification is mandatory**: for core keywords with small hit counts, eyeball every hit context. Known false-positive patterns — homographs (Korean 원서 = job application vs. original-language book), verb conjugations (anime = conjugation of French animer), metaphorical idioms ("translate vision into..."), place names (Promenade des Anglais). Report excluded false positives honestly in the report.

## Stage 2: Qualitative close reading

Pull signal-bearing personas per segment and **close-read 30+ in full**. Goal: find what percentages cannot tell you — triggers, usage contexts, payment psychology, churn points — in the actual narratives. Collect quotes for scenarios at this stage (persona text verbatim, with occupation and age noted).

## Stage 3: 7-section structured report (≤120 lines)

No introduction, conclusion, or disclaimers — exactly this order:

1. **Sample demographic snapshot** — only the distinctive features of age/education/occupation distributions, 3–4 sentences
2. **Target segment quantification** — table: segment | % (n) | representative evidence keywords with real counts. Include excluded false positives
3. **5–7 representative use-case scenarios** — each: real quote (occupation, age) + trigger + usage flow (in product-feature units) + frequency + willingness to pay + churn risk. One counter-example (anti-persona) recommended
4. **Strengths in this market** 3–5
5. **Weaknesses/blockers** 3–5
6. **Willingness-to-pay reading** — verdict across pricing-structure alternatives, with evidence
7. **1–2 killer insights** — findings visible only in this market that change what you would do

## Rules

- **No fabricated numbers**: every % comes only from Stage 1 script output. Market-knowledge inference (device penetration, payment culture) must be labeled "inference".
- **The brief is the entirety of the facts**: assume only the features/pricing/weaknesses written in the brief. No scenarios assuming features absent from the brief.
- **Synthetic-data limits**: personas are population composition, not behavioral logs. Write conclusions as "directional hypotheses".
