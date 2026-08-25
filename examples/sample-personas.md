# Sample personas — moved to Hugging Face

The n=1,000/country sample JSONL files previously stored here have been removed from
the git repo. Raw persona records (even synthetic ones) are structured like personal
data and are better served from the dataset platform:

- **Lite pack (10 countries × 10k rows, CC-BY-4.0)**: https://huggingface.co/datasets/dominicDK94/nemotron-personas-lite
- Reproduce the exact seed-42 samples used by the example runs:
  `scripts/sample_personas.py --n 1000 --seed 42` (see `scripts/setup_data.py`)
- Source: NVIDIA Nemotron-Personas (synthetic, CC-BY-4.0, attribution in root README)

The example research outputs in `examples/quest15/` and `examples/triproll/` are unchanged.
