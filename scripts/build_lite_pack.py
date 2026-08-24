#!/usr/bin/env python3
"""Nemotron-Personas 풀 데이터(~24GB) → 라이트 팩(~65MB) 빌더.

원본 10개국 parquet에서 국가당 N행(기본 10,000)을 시드 고정 추출해,
persona-lightsim 하네스가 실제로 소비하는 형태로 줄인다:
- 26개 컬럼 중 스킬이 읽는 15개만 유지 (바이트 기준 ~50% 절감)
- 긴 서사 필드는 300~400자로 트림 (샘플러의 TRIM과 동일 규칙)
- 원본 샤드 구조·파일명 유지 → 기존 sample_personas.py가 무수정으로 동작
  (벨기에 언어 쿼터 샤드 ??_BE.parquet, 인도 en_IN-* 필터 포함)

이 스크립트는 팩 배포자만 실행한다. 사용자는 scripts/setup_data.py로
완성된 팩을 HuggingFace에서 받는다.

사용:
  <pyarrow가 있는 python> build_lite_pack.py --base <풀 데이터 부모 디렉토리> \
      --out build/lite --n 10000 --seed 42
"""
import argparse
import glob
import hashlib
import json
import os
import random
import sys

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except ModuleNotFoundError:
    sys.exit("pyarrow 필요: uv run --with pyarrow python3 " + " ".join(sys.argv))

WANT = ['persona', 'professional_persona', 'arts_persona', 'hobbies_and_interests_list',
        'skills_and_expertise_list', 'career_goals_and_ambitions', 'sex', 'age',
        'marital_status', 'education_level', 'occupation', 'province', 'district',
        'country', 'cultural_background']
TRIM = {'persona': 400, 'professional_persona': 400, 'arts_persona': 400,
        'career_goals_and_ambitions': 300, 'cultural_background': 300}


def shards_for(country_dir):
    """sample_personas.py와 동일한 샤드 선택 규칙 — 반드시 동기화 유지."""
    name = os.path.basename(country_dir)
    if 'belgium' in name:
        return sorted(glob.glob(os.path.join(country_dir, '[a-z][a-z]_BE.parquet')))
    if 'india' in name:
        return sorted(glob.glob(os.path.join(country_dir, 'en_IN-*.parquet')))
    return sorted(glob.glob(os.path.join(country_dir, 'train-*.parquet')))


def sample_shard(path, take, rng):
    f = pq.ParquetFile(path)
    cols = [c for c in WANT if c in f.schema_arrow.names]
    ngroups = f.metadata.num_row_groups
    per_group = {}
    for _ in range(take):
        g = rng.randrange(ngroups)
        per_group[g] = per_group.get(g, 0) + 1
    rows = []
    for g in sorted(per_group):
        tbl = f.read_row_group(g, columns=cols)
        idxs = rng.sample(range(tbl.num_rows), min(per_group[g], tbl.num_rows))
        for i in idxs:
            row = {c: tbl.column(c)[i].as_py() for c in cols}
            for c, lim in TRIM.items():
                if isinstance(row.get(c), str) and len(row[c]) > lim:
                    row[c] = row[c][:lim] + '…'
            rows.append(row)
    rng.shuffle(rows)
    return rows, cols


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', required=True, help='nemotron-personas-* 풀 데이터의 부모 디렉토리')
    ap.add_argument('--out', required=True)
    ap.add_argument('--n', type=int, default=10000, help='국가당 행수')
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    manifest = {'version': 1, 'seed': args.seed, 'n_per_country': args.n,
                'columns': WANT, 'trim': TRIM,
                'source': 'nvidia Nemotron-Personas (HuggingFace, CC-BY-4.0)',
                'files': []}

    dirs = sorted(glob.glob(os.path.join(os.path.abspath(args.base), 'nemotron-personas-*')))
    if not dirs:
        raise SystemExit(f"no datasets under {args.base}")
    for d in dirs:
        cdir = os.path.basename(d)
        shards = shards_for(d)
        if not shards:
            print(f"{cdir}: NO SHARDS — 스킵")
            continue
        sizes = [pq.ParquetFile(s).metadata.num_rows for s in shards]
        total = sum(sizes)
        os.makedirs(os.path.join(args.out, cdir), exist_ok=True)
        c_rows = 0
        for s, sz in zip(shards, sizes):
            take = max(1, round(args.n * sz / total))
            rows, cols = sample_shard(s, take, rng)
            tbl = pa.Table.from_pylist(rows)
            # 컬럼 순서를 WANT 순으로 고정
            tbl = tbl.select([c for c in WANT if c in tbl.column_names])
            out_path = os.path.join(args.out, cdir, os.path.basename(s))
            pq.write_table(tbl, out_path, compression='zstd', row_group_size=1000)
            manifest['files'].append({
                'path': f"{cdir}/{os.path.basename(s)}",
                'rows': len(rows), 'bytes': os.path.getsize(out_path),
                'sha256': sha256(out_path), 'source_rows': sz,
            })
            c_rows += len(rows)
        print(f"{cdir}: {c_rows} rows from {total:,}")

    mpath = os.path.join(args.out, 'manifest.json')
    with open(mpath, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    total_bytes = sum(x['bytes'] for x in manifest['files'])
    print(f"done: {len(manifest['files'])} files, {total_bytes/1e6:.1f}MB -> {args.out}")


if __name__ == '__main__':
    main()
