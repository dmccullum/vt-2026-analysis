#!/bin/sh
# Rebuild everything from the raw files in data/raw (no network needed).
set -e
cd "$(dirname "$0")"
python3 -I scripts/parse_sos.py data/raw/sos2026 data/processed/2026
python3 -I scripts/parse_sos.py data/raw/sos2024 data/processed/2024
uv run python scripts/fetch_demographics.py
uv run python scripts/analyze.py
uv run python scripts/gov_models.py > data/processed/gov_models.txt
uv run python scripts/class_geo.py > data/processed/class_geo.txt
uv run python scripts/controls.py > data/processed/controls.txt
uv run python scripts/edu_income.py > data/processed/edu_income.txt
uv run python scripts/schools.py > data/processed/schools.txt
uv run python scripts/taxes.py > data/processed/taxes.txt
uv run python scripts/build_viz.py
