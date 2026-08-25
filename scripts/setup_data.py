#!/usr/bin/env python3
"""persona-lightsim data setup - download the HuggingFace lite pack + set up the runtime env.

What it does:
1. Downloads the file list pinned in scripts/data_manifest.json from HuggingFace
   into data/nemotron-personas-<country>/ (sha256-verified, resumable)
2. Creates the data/.venv-personas virtualenv and installs pyarrow (skip with --no-venv)

Standard library only - runs with bare python3:
  python3 scripts/setup_data.py                     # all 10 countries (~63MB)
  python3 scripts/setup_data.py --countries korea,japan
  python3 scripts/setup_data.py --no-venv

If you need the full data (0.1-8.9GB per country, 26 columns, untrimmed),
download the NVIDIA originals instead and point NEMOTRON_PERSONAS_BASE at
them - see the README.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(REPO_ROOT, 'scripts', 'data_manifest.json')
HF_DATASET = os.environ.get('PERSONA_LITE_DATASET', 'dominicDK94/nemotron-personas-lite')
BASE_URL = f"https://huggingface.co/datasets/{HF_DATASET}/resolve/main"


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def download(url, dest, expect_sha, expect_bytes):
    if os.path.exists(dest) and sha256(dest) == expect_sha:
        return 'cached'
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + '.part'
    req = urllib.request.Request(url, headers={'User-Agent': 'persona-lightsim-setup'})
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp, 'wb') as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    if os.path.getsize(tmp) != expect_bytes or sha256(tmp) != expect_sha:
        os.remove(tmp)
        raise RuntimeError(f"checksum mismatch: {url}")
    os.replace(tmp, dest)
    return 'downloaded'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--countries', default='', help='comma-separated (e.g. korea,japan); empty = all')
    ap.add_argument('--data-dir', default=os.path.join(REPO_ROOT, 'data'))
    ap.add_argument('--no-venv', action='store_true')
    args = ap.parse_args()

    if 'PLACEHOLDER' in HF_DATASET:
        sys.exit("HF_DATASET is not configured yet (pre-release repo). "
                 "Set the PERSONA_LITE_DATASET env var or contact the maintainer.")

    manifest = json.load(open(MANIFEST, encoding='utf-8'))
    wanted = {c.strip().lower() for c in args.countries.split(',') if c.strip()}

    files = []
    for f in manifest['files']:
        country = f['path'].split('/')[0].replace('nemotron-personas-', '')
        if wanted and country not in wanted:
            continue
        files.append(f)
    if not files:
        sys.exit(f"no such countries in the manifest: {sorted(wanted)}")

    total_mb = sum(f['bytes'] for f in files) / 1e6
    print(f"lite pack download: {len(files)} files, {total_mb:.1f}MB -> {args.data_dir}")
    for i, f in enumerate(files, 1):
        dest = os.path.join(args.data_dir, f['path'])
        status = download(f"{BASE_URL}/{f['path']}", dest, f['sha256'], f['bytes'])
        print(f"  [{i}/{len(files)}] {f['path']} ({f['bytes']//1024}KB) {status}")

    venv_python_rel = os.path.join('Scripts', 'python.exe') if os.name == 'nt' else os.path.join('bin', 'python')

    if not args.no_venv:
        venv = os.path.join(args.data_dir, '.venv-personas')
        py = os.path.join(venv, venv_python_rel)
        if not os.path.exists(py):
            print(f"creating venv: {venv}")
            subprocess.run([sys.executable, '-m', 'venv', venv], check=True)
        subprocess.run([py, '-m', 'pip', 'install', '-q', 'pyarrow'], check=True)
        print("pyarrow installed")

    print("\nSetup complete. Smoke test:")
    print(f"  {os.path.join(args.data_dir, '.venv-personas', venv_python_rel)} "
          ".claude/skills/persona-research/scripts/sample_personas.py "
          f"--base {args.data_dir} --countries korea --n 30 --seed 7 --out /tmp/persona-smoke")


if __name__ == '__main__':
    main()
