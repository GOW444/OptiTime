#!/usr/bin/env python3
"""
model_core.py
OptiTime - MILP core with informative prints, robust variable naming,
solver attempts (CBC -> GLPK -> greedy), and result saving.

Drop-in to your OptiTime project. Expects data files under ./data/ and writes under ./results/.
"""

import os
import csv
import json
import sys
import time
import traceback
from collections import Counter, defaultdict
import re

try:
    import pulp
except Exception as e:
    print("ERROR: pulp not installed. Run: pip install pulp")
    raise

# ---------------------------
# Helper I/O and utils
# ---------------------------
DATA_DIR = "data"
RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

def read_csv(filepath):
    rows = []
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({k: v.strip() for k, v in r.items()})
    return rows

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_csv(path, rows, fieldnames):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

def save_json(path, obj):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=2)

def _sanitize(s):
    return re.sub(r'[^0-9A-Za-z_]', '_', str(s))

# ---------------------------
# Timeslot loader (optional file)
# ---------------------------
def load_timeslots(default_count=10):
    """
    Load timeslots from data/timeslots.csv (header 'timeslot_id') or data/timeslots.json (list).
    If none found, return default t1..tN list.
    """
    csv_path = os.path.join(DATA_DIR, "timeslots.csv")
    json_path = os.path.join(DATA_DIR, "timeslots.json")
    if os.path.exists(csv_path):
        try:
            rows = read_csv(csv_path)
            ts = [r.get("timeslot_id") or r.get("id") or r.get("timeslot") for r in rows]
            ts = [t for t in ts if t]
            if ts:
                print(f"[IO] Loaded {len(ts)} timeslots from {csv_path}")
                return ts
        except Exception as e:
            print(f"[IO][WARN] Failed to read {csv_path}: {e}")
    if os.path.exists(json_path):
        try:
            data = load_json(json_path)
            if isinstance(data, list) and data:
                print(f"[IO] Loaded {len(data)} timeslots from {json_path}")
                return data
        except Exception as e:
            print(f"[IO][WARN] Failed to read {json_path}: {e}")
    # fallback
    ts = [f"t{i+1}" for i in range(default_count)]
    print(f"[MAIN] No timeslot file found — using default {len(ts)} timeslots: {ts}")
    return ts

# ---------------------------
# Data loading
# ---------------------------
def load_all_data():
    print("[IO] Loading data files from", DATA_DIR)
    courses_f = os.path.join(DATA_DIR, "courses.csv")
    rooms_f = os.path.join(DATA_DIR, "rooms.csv")
    enrolls_f = os.path.join(DATA_DIR, "enrollments.csv")
    allowed_rooms_f = os.path.join(DATA_DIR, "allowed_rooms.json")
    conflict_matrix_f = os.path.join(DATA_DIR, "conflict_matrix.json")

    courses = read_csv(courses_f) if os.path.exists(courses_f) else []
    rooms = read_csv(rooms_f) if os.path.exists(rooms_f) else []
    enrollments = read_csv(enrolls_f) if os.path.exists(enrolls_f) else []
    allowed_rooms = load_json(allowed_rooms_f) if os.path.exists(allowed_rooms_f) else {}
    conflict_matrix = load_json(conflict_matrix_f) if os.path.exists(conflict_matrix_f) else {}

    print(f"[IO] Loaded: {len(courses)} course rows, {len(rooms)} room rows, {len(enrollments)} enrollment rows")
    return courses, rooms, enrollments, allowed_rooms, conflict_matrix

# ---------------------------
# Build model
# ---------------------------
def build_milp_model(courses, rooms, enrollments, allowed_rooms, conflict_matrix, timeslots):
    """
    Build a MILP model like your template.
    Returns: prob, x, y, C, T, R
    """
    print("[MILP] Initializing problem...")
    prob = pulp.LpProblem("OptiTime_MILP", pulp.LpMinimize)

    # Normalize/derive domain lists
    C = [row.get("course_id") or row.get("id") or row.get("course") for row in courses]
    for i, row in enumerate(courses):
        if not row.get("course_id") and row.get("id"):
            C[i] = row.get("id")
        if C[i] is None:
            C[i] = f"COURSE_{i}"

    R = [row.get("room_id") or row.get("id") or row.get("room") for row in rooms]
    for i, row in enumerate(rooms):
        if not R[i]:
            R[i] = f"ROOM_{i}"

    T = list(timeslots)

    # Diagnostics for duplicates / sanitization collisions
    print("[MILP] Checking duplicates and sanitization collisions...")
    dupC = [k for k,v in Counter(C).items() if v>1]
    dupR = [k for k,v in Counter(R).items() if v>1]
    dupT = [k for k,v in Counter(T).items() if v>1]
    if dupC or dupR or dupT:
        print(f"[MILP][WARN] duplicates detected: courses={dupC if dupC else 'none'}, rooms={dupR if dupR else 'none'}, times={dupT if dupT else 'none'}")

    sanC = [_sanitize(x) for x in C]
    sanR = [_sanitize(x) for x in R]
    sanT = [_sanitize(x) for x in T]

    def show_collisions(orig, san, label):
        collisions = defaultdict(list)
        for o, s in zip(orig, san):
            collisions[s].append(o)
        collisions = {k:v for k,v in collisions.items() if len(v)>1}
        if collisions:
            print(f"[MILP][WARN] sanitization collisions in {label}:")
            for k, v in collisions.items():
                print(f"   {k}: {v}")

    show_collisions(C, sanC, "Courses")
    show_collisions(R, sanR, "Rooms")
    show_collisions(T, sanT, "Times")

    # de-duplicate input domain lists while preserving order
    C = list(dict.fromkeys(C))
    R = list(dict.fromkeys(R))
    T = list(dict.fromkeys(T))
    print(f"[MILP] Domain sizes after dedupe: |C|={len(C)}, |T|={len(T)}, |R|={len(R)}")

    # create lookup maps for capacities
    room_capacity = {}
    for row in rooms:
        rid = row.get("room_id") or row.get("room") or row.get("id")
        if rid is None:
            continue
        cap = row.get("capacity")
        try:
            room_capacity[rid] = int(cap) if cap is not None and str(cap).strip() != "" else None
        except:
            room_capacity[rid] = None

    # Build variables with index-based names (guaranteed unique)
    print("[MILP] Creating decision variables (index-based names)...")
    x = {}   # x[c][t][r] binary: course c at time t in room r
    for ci, c in enumerate(C):
        x[c] = {}
        for ti, t in enumerate(T):
            x[c][t] = {}
            for ri, r in enumerate(R):
                varname = f"x_c{ci}_t{ti}_r{ri}"
                x[c][t][r] = pulp.LpVariable(varname, cat='Binary')

    y = None
    same_room_feature = True   # adjust as needed
    if same_room_feature:
        print("[MILP] Creating same-room linking variables y[c][r]...")
        y = {}
        for ci, c in enumerate(C):
            y[c] = {}
            for ri, r in enumerate(R):
                varname = f"y_c{ci}_r{ri}"
                y[c][r] = pulp.LpVariable(varname, cat='Binary')

    # A few quick counts
    num_x = sum(1 for c in x for t in x[c] for r in x[c][t])
    num_y = sum(1 for c in (y or {}) for r in (y[c] or {})) if y else 0
    print(f"[MILP] Created variables: x={num_x}, y={num_y}")

    # --------------------------
    # Add constraints
    # --------------------------
    print("[MILP] Adding constraints and objective (this section can be extended with your custom constraints)...")

    # 1) Each course must be assigned to exactly one (time, room) pair (coverage)
    for c in C:
        prob += pulp.lpSum(x[c][t][r] for t in T for r in R) == 1, f"cover_{_sanitize(c)}"

    # 2) Allowed rooms: disable (force 0) for disallowed rooms if allowed_rooms provided
    if allowed_rooms:
        for c in C:
            allowed = set(allowed_rooms.get(c, allowed_rooms.get(str(c), R)))  # fallback
            if not allowed:
                continue
            disallowed = [r for r in R if r not in allowed]
            for t in T:
                for r in disallowed:
                    prob += x[c][t][r] == 0, f"not_allowed_{_sanitize(c)}_{_sanitize(t)}_{_sanitize(r)}"

    # 3) Room capacity constraint based on enrollments if capacity information exists
    course_demand = Counter()
    for e in enrollments:
        cid = e.get("course_id") or e.get("course") or e.get("id")
        if cid is None:
            continue
        course_demand[cid] += 1

    for c in C:
        demand = course_demand.get(c, 0)
        if demand == 0:
            continue
        for t in T:
            for r in R:
                cap = room_capacity.get(r)
                if cap is None:
                    continue
                if cap < demand:
                    prob += x[c][t][r] == 0, f"cap_block_{_sanitize(c)}_{_sanitize(t)}_{_sanitize(r)}"

    # 4) Student conflict constraints using conflict_matrix
    if conflict_matrix:
        print("[MILP] Adding student conflict constraints from conflict_matrix.json")
        for c in C:
            conflicts = conflict_matrix.get(c, conflict_matrix.get(str(c), []))
            for c2 in conflicts:
                if c2 not in C:
                    continue
                for t in T:
                    prob += pulp.lpSum(x[c][t][r] for r in R) + pulp.lpSum(x[c2][t][r2] for r2 in R) <= 1, f"conflict_{_sanitize(c)}_{_sanitize(c2)}_{_sanitize(t)}"

    # 5) Linking x and y variables if y is used
    if y:
        for c in C:
            for r in R:
                for t in T:
                    prob += x[c][t][r] <= y[c][r], f"link_x_y_{_sanitize(c)}_{_sanitize(t)}_{_sanitize(r)}"
            prob += pulp.lpSum(y[c][r] for r in R) <= 1, f"one_room_overall_{_sanitize(c)}"

    # 6) Room occupancy: at most one course per room per timeslot
    for t in T:
        for r in R:
            prob += pulp.lpSum(x[c][t][r] for c in C) <= 1, f"room_once_{_sanitize(t)}_{_sanitize(r)}"

    # --------------------------
    # Objective: default heuristic objective (replace with your own)
    # --------------------------
    print("[MILP] Adding objective function (example default objective used — replace with real objective if needed).")
    room_index = {r: i for i, r in enumerate(R)}
    obj = pulp.lpSum(room_index[r] * x[c][t][r] for c in C for t in T for r in R)
    prob += obj

    print("[MILP] Finished building model.")
    return prob, x, y, C, T, R

# ---------------------------
# Solver attempt logic
# ---------------------------
def try_solve_with_solvers(prob, timeout=None):
    """
    Try CBC then GLPK. Return (success_bool, solver_name_or_info, time_taken, solver_error).
    """
    solvers_tried = []

    # 1) Try CBC (PULP_CBC_CMD). Allow user to override CBC path via env var OPTITIME_CBC_PATH
    try:
        print("Trying CBC...")
        t0 = time.time()
        cbc_path = os.environ.get("OPTITIME_CBC_PATH", None)  # optionally provide path to compatible CBC binary
        if cbc_path:
            solver = pulp.PULP_CBC_CMD(path=cbc_path, msg=True, timeLimit=timeout if timeout else None)
        else:
            solver = pulp.PULP_CBC_CMD(msg=True, timeLimit=timeout if timeout else None)
        res = prob.solve(solver)
        t1 = time.time()
        status = pulp.LpStatus.get(prob.status, "Unknown") if isinstance(pulp.LpStatus, dict) else pulp.LpStatus[prob.status]
        print(f"CBC result: status={status}")
        if isinstance(status, str) and status.lower().startswith("optimal"):
            return True, "CBC", t1 - t0, None
        else:
            solvers_tried.append(("CBC", str(status)))
            print("[MILP][CBC] solver status:", status)
    except Exception as e:
        tb = traceback.format_exc()
        print("CBC FAILED:\n", tb)
        solvers_tried.append(("CBC", str(e)))

    # 2) Try GLPK
    try:
        print("Trying GLPK...")
        t0 = time.time()
        opts = ['--tmlim', str(timeout)] if timeout else []
        solver = pulp.GLPK_CMD(msg=True, options=opts if opts else None)
        res = prob.solve(solver)
        t1 = time.time()
        status = pulp.LpStatus.get(prob.status, "Unknown") if isinstance(pulp.LpStatus, dict) else pulp.LpStatus[prob.status]
        print(f"GLPK result: status={status}")
        if isinstance(status, str) and status.lower().startswith("optimal"):
            return True, "GLPK", t1 - t0, None
        else:
            solvers_tried.append(("GLPK", str(status)))
            print("[MILP][GLPK] solver status:", status)
    except Exception as e:
        tb = traceback.format_exc()
        print("GLPK FAILED:\n", tb)
        solvers_tried.append(("GLPK", str(e)))

    return False, solvers_tried, None, None

# ---------------------------
# Greedy fallback solver (simple)
# ---------------------------
def greedy_solver(C, T, R, allowed_rooms, room_capacity, course_demand, conflict_matrix):
    """
    Very simple greedy: iterate courses, try assign earliest timeslot & first allowed room with capacity.
    Avoid time conflicts based on conflict_matrix (courses listed cannot share a timeslot).
    """
    print("[GREEDY] Starting greedy solver...")
    assignments = {}  # c -> (t, r)
    room_time_taken = set()  # (t, r) assigned

    # ordering heuristic: sort by demand descending (bigger classes first)
    order = sorted(C, key=lambda c: -course_demand.get(c, 0))

    for c in order:
        assigned = False
        allowed = allowed_rooms.get(c, allowed_rooms.get(str(c), R)) or R
        confs = conflict_matrix.get(c, conflict_matrix.get(str(c), []))
        for t in T:
            # check conflicts: if some already-assigned course that conflicts with c is in timeslot t, skip
            conflict_here = False
            for other in confs:
                if other in assignments and assignments[other][0] == t:
                    conflict_here = True
                    break
            if conflict_here:
                continue
            for r in allowed:
                if (t, r) in room_time_taken:
                    continue
                cap = room_capacity.get(r)
                if cap is not None and cap < course_demand.get(c, 0):
                    continue
                # assign
                assignments[c] = (t, r)
                room_time_taken.add((t, r))
                assigned = True
                break
            if assigned:
                break
        if not assigned:
            # last resort: ignore allowed rooms/capacity and pick first free slot
            for t in T:
                for r in R:
                    if (t, r) in room_time_taken:
                        continue
                    assignments[c] = (t, r)
                    room_time_taken.add((t, r))
                    assigned = True
                    break
                if assigned:
                    break
        if not assigned:
            assignments[c] = (None, None)
    print("[GREEDY] finished assignments for", len(assignments), "courses")
    return assignments

# ---------------------------
# Save results helper
# ---------------------------
def save_assignments(assignments_map, out_csv):
    rows = []
    for c, pair in assignments_map.items():
        t, r = pair
        rows.append({"course_id": c, "timeslot": t, "room_id": r})
    fieldnames = ["course_id", "timeslot", "room_id"]
    save_csv(out_csv, rows, fieldnames)
    print(f"[IO] Saved assignments to {out_csv}")

# ---------------------------
# Main runner
# ---------------------------
def main():
    courses, rooms, enrollments, allowed_rooms, conflict_matrix = load_all_data()

    # Load timeslots (from file if present), else default t1..t10
    timeslots = load_timeslots(default_count=10)

    prob, x, y, C, T, R = build_milp_model(courses, rooms, enrollments, allowed_rooms, conflict_matrix, timeslots)

    # Try to solve using CBC/GLPK
    solved, solver_info, tsolve, _ = try_solve_with_solvers(prob, timeout=300)
    if solved:
        solver_name = solver_info
        print(f"[MAIN] Solved by {solver_name}")
        # Extract solution
        assignments = {}
        for c in C:
            assigned = False
            for t in T:
                for r in R:
                    var = x[c][t][r]
                    try:
                        val = var.value()
                    except Exception:
                        val = pulp.value(var)
                    if val is not None and float(val) > 0.5:
                        assignments[c] = (t, r)
                        assigned = True
                        break
                if assigned:
                    break
            if not assigned:
                assignments[c] = (None, None)
        out_csv = os.path.join(RESULTS_DIR, "assignments_milp.csv")
        save_assignments(assignments, out_csv)
        metrics = {"solver": solver_name, "time_sec": tsolve, "num_courses": len(C)}
        save_json(os.path.join(RESULTS_DIR, "metrics_milp.json"), metrics)
        print("[MAIN] MILP assignments and metrics saved.")
        return

    # If here, solvers failed -> greedy fallback
    print("[MAIN] MILP Solvers failed. Falling back to greedy solver.")
    # Build helpers for greedy
    room_capacity = {}
    for row in rooms:
        rid = row.get("room_id") or row.get("room") or row.get("id")
        cap = row.get("capacity")
        try:
            room_capacity[rid] = int(cap) if cap is not None and str(cap).strip() != "" else None
        except:
            room_capacity[rid] = None

    course_demand = Counter()
    for e in enrollments:
        cid = e.get("course_id") or e.get("course") or e.get("id")
        if cid is None:
            continue
        course_demand[cid] += 1

    assignments = greedy_solver(C, T, R, allowed_rooms, room_capacity, course_demand, conflict_matrix)
    out_csv = os.path.join(RESULTS_DIR, "assignments_greedy.csv")
    save_assignments(assignments, out_csv)
    metrics = {"solver": "greedy", "time_sec": None, "num_courses": len(C)}
    save_json(os.path.join(RESULTS_DIR, "metrics_greedy.json"), metrics)
    print("[MAIN] Greedy assignments and metrics saved.")

if __name__ == "__main__":
    main()
