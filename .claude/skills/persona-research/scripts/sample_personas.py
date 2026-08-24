#!/usr/bin/env python3
"""Nemotron-Personas parquet -> per-country sample JSONL sampler.

- Shard-size-proportional allocation, then random row-group extraction
  (never loads a whole file into memory)
- Reproducible with a fixed seed
- Long narrative fields are trimmed to keep samples at ~2MB per country
- Data location: defaults to data/ at the repo root (populated by
  scripts/setup_data.py). Override with the NEMOTRON_PERSONAS_BASE env var
  or --base. Works identically on the lite pack (10k rows/country) and the
  full NVIDIA datasets.

Usage (run through the dedicated venv - bare python3 may lack pyarrow):
  data/.venv-personas/bin/python sample_personas.py --n 1000 --seed 42 --out ./personas
  data/.venv-personas/bin/python sample_personas.py --countries korea,japan --n 30 --seed 7 --out /tmp/smoke
  # without a venv: uv run --with pyarrow python3 sample_personas.py ...

Dependencies: pyarrow (no pandas).
"""
import argparse
import glob
import json
import os
import random
import sys

try:
    import pyarrow.parquet as pq
except ModuleNotFoundError:
    sys.exit(
        "This python has no pyarrow. Re-run with one of:\n"
        "  data/.venv-personas/bin/python " + " ".join(sys.argv) + "\n"
        "  uv run --with pyarrow python3 " + " ".join(sys.argv) + "\n"
        "  (create venv: python3 -m venv data/.venv-personas && data/.venv-personas/bin/pip install pyarrow)"
    )

DEFAULT_BASE = os.environ.get('NEMOTRON_PERSONAS_BASE') or os.path.join(
    os.path.dirname(__file__), '..', '..', '..', '..', 'data')

WANT = ['persona', 'professional_persona', 'arts_persona', 'hobbies_and_interests_list',
        'skills_and_expertise_list', 'career_goals_and_ambitions', 'sex', 'age',
        'marital_status', 'education_level', 'occupation', 'province', 'district',
        'country', 'cultural_background']
TRIM = {'persona': 400, 'professional_persona': 400, 'arts_persona': 400,
        'career_goals_and_ambitions': 300, 'cultural_background': 300}


def shards_for(country_dir):
    """Per-country shard selection. Belgium: language-quota shards (de/en/fr/nl); India: English personas only."""
    name = os.path.basename(country_dir)
    if 'belgium' in name:
        return sorted(glob.glob(os.path.join(country_dir, '[a-z][a-z]_BE.parquet')))
    if 'india' in name:
        return sorted(glob.glob(os.path.join(country_dir, 'en_IN-*.parquet')))
    return sorted(glob.glob(os.path.join(country_dir, 'train-*.parquet')))


def sample_country(country_dir, n, rng):
    shards = shards_for(country_dir)
    if not shards:
        return None, 0
    sizes = [pq.ParquetFile(s).metadata.num_rows for s in shards]
    total = sum(sizes)
    out_rows = []
    for s, sz in zip(shards, sizes):
        take = max(1, round(n * sz / total))
        f = pq.ParquetFile(s)
        cols = [c for c in WANT if c in f.schema_arrow.names]
        ngroups = f.metadata.num_row_groups
        per_group = {}
        for _ in range(take):
            g = rng.randrange(ngroups)
            per_group[g] = per_group.get(g, 0) + 1
        for g, k in per_group.items():
            tbl = f.read_row_group(g, columns=cols)
            idxs = rng.sample(range(tbl.num_rows), min(k, tbl.num_rows))
            for i in idxs:
                row = {c: tbl.column(c)[i].as_py() for c in cols}
                for c, lim in TRIM.items():
                    if isinstance(row.get(c), str) and len(row[c]) > lim:
                        row[c] = row[c][:lim] + '…'
                out_rows.append(row)
    rng.shuffle(out_rows)
    return out_rows[:n], total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default=DEFAULT_BASE, help='parent of the nemotron-personas-* directories')
    ap.add_argument('--countries', default='', help='comma-separated (e.g. korea,japan); empty = all')
    ap.add_argument('--n', type=int, default=1000, help='sample size per country')
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--out', required=True, help='output directory')
    args = ap.parse_args()

    base = os.path.abspath(args.base)
    os.makedirs(args.out, exist_ok=True)
    wanted = {c.strip().lower() for c in args.countries.split(',') if c.strip()}
    rng = random.Random(args.seed)

    dirs = sorted(glob.glob(os.path.join(base, 'nemotron-personas-*')))
    if not dirs:
        raise SystemExit(
            f"no datasets under {base}\n"
            "no data yet? from the repo root, first run: python3 scripts/setup_data.py")
    for d in dirs:
        cname = os.path.basename(d).replace('nemotron-personas-', '')
        if wanted and cname not in wanted:
            continue
        rows, total = sample_country(d, args.n, rng)
        if rows is None:
            print(f"{cname}: NO SHARDS - skipped")
            continue
        path = os.path.join(args.out, f"{cname}.jsonl")
        with open(path, 'w', encoding='utf-8') as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + '\n')
        print(f"{cname}: sampled={len(rows)} from {total:,} rows -> {path} "
              f"({os.path.getsize(path) // 1024}KB)")


if __name__ == '__main__':
    main()
