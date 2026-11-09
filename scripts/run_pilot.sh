#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ -e runs/pilot/train-512.json ] || [ -e runs/pilot/train-1024.json ]; then
  echo 'Pilot results already exist. Archive runs/pilot and its configs before rerunning.' >&2
  exit 1
fi
.venv/bin/python scripts/download_model.py
.venv/bin/python scripts/prepare_pilot.py > runs/pilot/data-lengths.jsonl
.venv/bin/python scripts/measure.py inference -- .venv/bin/python scripts/inference_pilot.py
.venv/bin/python scripts/measure.py train-512 -- .venv/bin/python scripts/train_pilot.py --config configs/pilot-512.yaml
.venv/bin/python scripts/measure.py train-1024 -- .venv/bin/python scripts/train_pilot.py --config configs/pilot-1024.yaml
.venv/bin/python scripts/measure.py adapter-reload -- .venv/bin/python scripts/inference_pilot.py --adapter runs/pilot/adapters/1024

.venv/bin/python scripts/summarize_pilot.py
