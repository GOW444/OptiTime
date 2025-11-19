# model_core.py
# MILP timetable with automatic solver fallback (CBC → GLPK → Greedy)

import pandas as pd
import pulp
import json
from pathlib import Path
from collections import defaultdict
import traceback

DATA = Path("data")
RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

# Save function
def _save(assigns_df, metrics):
    assigns_df.to_csv(RESULTS / "assignments_milp.csv", index=False)
    with open(RESULTS / "metrics_milp.json", "w") as f:
        json.dump(metrics, f, indent=2)

# Greedy fallback
def _run_greedy():
    from greedy import run_greedy
    assigns_df, metrics = run_greedy()
    _save(assigns_df, metrics)
    return assigns_df, metrics

# Main
def build_and_solve(timeslots=None, same_room=True, solver_msg=False):

    # Load data
    courses = pd.read_csv(DATA / "courses.csv")
    rooms = pd.read_csv(DATA / "rooms.csv")
    enroll = pd.read_csv(DATA / "enrollments.csv")

    C = list(courses["course_id"])
    R = list(rooms["room"])
    T = timeslots if timeslots else [f"t{i}" for i in range(1, 11)]

    h = {row["course_id"]: int(row["slots_required"]) for _, row in courses.iterrows()}
    enroll_counts = enroll["course_id"].value_counts().to_dict()

    # Allowed rooms: read file if exists, else build from capacity
    allowed_path = DATA / "allowed_rooms.json"
    if allowed_path.exists():
        with open(allowed_path) as f:
            allowed_rooms = json.load(f)
    else:
        allowed_rooms = {
            c: [
                r
                for r, cap in zip(rooms["room"], rooms["capacity"])
                if enroll_counts.get(c, 0) == 0 or cap >= enroll_counts.get(c, 0)
            ]
            for c in C
        }

    # Build conflict matrix
    students = enroll.groupby("student_id")["course_id"].apply(list).to_dict()
    conflict = defaultdict(dict)
    for st, clist in students.items():
        for i in range(len(clist)):
            for j in range(i + 1, len(clist)):
                c1, c2 = clist[i], clist[j]
                conflict[c1][c2] = 1
                conflict[c2][c1] = 1

    # Capacity lookup
    cap = dict(zip(rooms["room"], rooms["capacity"]))

    # MILP problem
    print("[MILP] Initializing problem...")
    prob = pulp.LpProblem('OptiTime', pulp.LpMinimize)

    print("[MILP] Creating decision variables...")
    x = pulp.LpVariable.dicts('x', (C, T, R), cat='Binary')
    y = pulp.LpVariable.dicts('y', (C, R), cat='Binary') if same_room else None

    print("[MILP] Adding same-room constraints...")
    if same_room:
        for c in C:
            prob += pulp.lpSum(y[c][r] for r in allowed_rooms.get(c, R)) == 1

    print("[MILP] Adding allowed-room & linking constraints...")
    for c in C:
        allowed = allowed_rooms.get(c, R)
        for t in T:
            for r in R:
                if r not in allowed:
                    prob += x[c][t][r] == 0
                    if same_room:
                        prob += y[c][r] == 0
                else:
                    if same_room:
                        prob += x[c][t][r] <= y[c][r]

    print("[MILP] Adding coverage constraints...")
    for c in C:
        prob += pulp.lpSum(x[c][t][r] for t in T for r in allowed_rooms.get(c, R)) == h[c]

    print("[MILP] Adding room occupancy constraints...")
    for t in T:
        for r in R:
            prob += pulp.lpSum(x[c][t][r] for c in C) <= 1

    print("[MILP] Adding student conflict constraints...")
    for i in range(len(C)):
        for j in range(i+1, len(C)):
            c1, c2 = C[i], C[j]
            if conflict.get(c1, {}).get(c2, 0) == 1:
                for t in T:
                    prob += pulp.lpSum(x[c1][t][r] for r in allowed_rooms.get(c1, R)) + \
                            pulp.lpSum(x[c2][t][r] for r in allowed_rooms.get(c2, R)) <= 1

    print("[MILP] Adding objective function...")
    prob += pulp.lpSum((cap[r] - enroll_counts.get(c, 0)) * x[c][t][r]
                        for c in C for t in T for r in allowed_rooms.get(c, R))

    print("[MILP] Finished building model.")
    print("[MILP] Starting solver...")


    x = pulp.LpVariable.dicts("x", (C, T, R), cat="Binary")
    y = pulp.LpVariable.dicts("y", (C, R), cat="Binary") if same_room else None

    # Same-room constraint
    if same_room:
        for c in C:
            prob += pulp.lpSum(y[c][r] for r in allowed_rooms[c]) == 1

    # X constraints + allowed rooms + linking
    for c in C:
        for t in T:
            for r in R:
                if r not in allowed_rooms[c]:
                    prob += x[c][t][r] == 0
                    if same_room:
                        prob += y[c][r] == 0
                else:
                    if same_room:
                        prob += x[c][t][r] <= y[c][r]

    # Course slot requirement
    for c in C:
        prob += pulp.lpSum(x[c][t][r] for t in T for r in allowed_rooms[c]) == h[c]

    # Room occupancy
    for t in T:
        for r in R:
            prob += pulp.lpSum(x[c][t][r] for c in C) <= 1

    # Student conflict constraint
    for c1 in C:
        for c2 in C:
            if c1 < c2 and conflict.get(c1, {}).get(c2, 0) == 1:
                for t in T:
                    prob += (
                        pulp.lpSum(x[c1][t][r] for r in allowed_rooms[c1])
                        + pulp.lpSum(x[c2][t][r] for r in allowed_rooms[c2])
                        <= 1
                    )

    # Objective: minimize unused seats
    prob += pulp.lpSum(
        (cap[r] - enroll_counts.get(c, 0)) * x[c][t][r]
        for c in C
        for t in T
        for r in allowed_rooms[c]
    )

    # ========== SOLVER BLOCK (with perfect fallback) ==========

    # 1) Try CBC
    try:
        print("Trying CBC...")
        prob.solve(pulp.GLPK_CMD(path="/opt/homebrew/bin/glpsol", msg=solver_msg))

    except Exception as e:
        print("\nCBC FAILED:")
        print(e)
        print("\nTrying GLPK...")
        try:
            prob.solve(pulp.GLPK_CMD(msg=solver_msg))
        except Exception as e2:
            print("\nGLPK FAILED too:")
            print(e2)
            print("\nFalling back to greedy method.")
            return _run_greedy()

    # =========================================================

    # Collect assignments
    assigns = []
    for c in C:
        for t in T:
            for r in allowed_rooms[c]:
                if pulp.value(x[c][t][r]) > 0.5:
                    assigns.append({"course_id": c, "timeslot": t, "room": r})

    assigns_df = pd.DataFrame(assigns)

    # Metrics
    course_times = assigns_df.groupby("course_id")["timeslot"].apply(list).to_dict()

    student_conflicts = 0
    for st, clist in students.items():
        seen = {}
        for c in clist:
            for t in course_times.get(c, []):
                seen[t] = seen.get(t, 0) + 1
        for t, cnt in seen.items():
            if cnt > 1:
                student_conflicts += (cnt - 1)

    total_assigned_seats = sum(
        enroll_counts.get(row["course_id"], 0) for _, row in assigns_df.iterrows()
    )
    total_capacity_used = sum(cap.get(row["room"], 0) for _, row in assigns_df.iterrows())
    util = (
        round(100 * total_assigned_seats / total_capacity_used, 2)
        if total_capacity_used > 0
        else 0.0
    )

    metrics = {
        "num_assignments": len(assigns_df),
        "student_conflicts": int(student_conflicts),
        "total_assigned_seats": int(total_assigned_seats),
        "total_capacity_used": int(total_capacity_used),
        "room_util_percent": util,
    }

    _save(assigns_df, metrics)
    print("MILP complete. Results saved.")
    return assigns_df, metrics


if __name__ == "__main__":
    build_and_solve(same_room=True, solver_msg=False)
