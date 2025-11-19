#!/usr/bin/env bash
set -e
python3 generate_data.py
python3 preprocess.py
# try MILP; if MILP fails, you can run greedy instead
python3 model_core.py
python3 validate.py
echo "Done. Check results/assignments_milp.csv and results/metrics_milp.json"
