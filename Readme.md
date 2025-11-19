# OptiTime — Day0 scaffold

## Setup (one-time)
python3 -m venv venv
source venv/bin/activate         # mac/linux
# .\venv\Scripts\activate        # windows powershell
pip install -r requirements.txt

## Run full pipeline
./run.sh

## Files produced
- data/courses.csv, rooms.csv, enrollments.csv
- data/conflict_matrix.json, data/allowed_rooms.json
- results/assignments_milp.csv, results/metrics_milp.json
- results/assignments_greedy.csv, results/metrics_greedy.json
