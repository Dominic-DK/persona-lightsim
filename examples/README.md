# Examples — real research runs / 실사용 산출물

Two complete, unedited research runs produced by this harness (2026-08-25), plus the exact
persona samples they were run against. Everything here is a **directional hypothesis**, not
market validation — see "Notes and limits" in the root README.

이 하네스로 실제 수행한 리서치 런 2건(2026-08-25, 무편집 원본)과 그때 사용한 표본이다.
모든 결론은 **방향 가설**이며 시장 검증이 아니다 — 루트 README의 "주의와 한계" 참조.

## Runs

| Run | Product under test | Files |
|---|---|---|
| [`quest15/`](quest15/) | Quest15 — location-based 10–15 min micro-quest iOS app (pre-launch POC) | audited product brief · 10 country analyst reports · cross-country synthesis · adversarial critic verdict |
| [`triproll/`](triproll/) | TripRoll — shared travel film-roll → auto-edited film iOS app (pre-launch) | same structure |

Each run: product brief audited against the actual codebase → 10 country analysts in parallel
(blind to each other) → cross-country synthesis → adversarial critic re-verification.
False-positive removal logs and reproduction script paths are preserved inside each report.

## Sample data

[`sample-personas/`](sample-personas/) — the n≈1,000-per-country samples (10 countries,
9,994 personas total) used by both runs. Drawn with `scripts/sample_personas.py --n 1000 --seed 42`
(shard-size-proportional random sampling), so the exact samples are reproducible from the
lite pack or the NVIDIA originals.

- Source: NVIDIA **Nemotron-Personas** country datasets (synthetic personas)
- License: **CC-BY-4.0** (© NVIDIA) — redistribution with attribution
- Caveat: narrative fields are trimmed to 300–400 chars by the sampler. Loss is ~0% for
  CJK (Korea/Japan) but 52–58% for Latin-script countries — **never compare percentages
  across countries directly.**
