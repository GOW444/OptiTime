import pandas as pd
import pulp
import json
from io import StringIO
import sys

# ==========================================
# 0. CONFIGURATION (Tunable Weights)
# ==========================================
W1_TIME_PENALTY = 5     
W2_PROF_OVERLOAD = 100  
PROF_DAILY_LIMIT = 2    
SOLVER_TIME_LIMIT = 100  # Stop after 30 seconds (CRITICAL FIX)

# ==========================================
# 1. LOAD DATA 
# ==========================================
print("Loading Data...")

try:
    df_courses = pd.read_csv('courses.csv')
    df_students = pd.read_csv('student_data_large.csv')
except FileNotFoundError:
    print("Error: CSV files not found.")
    sys.exit(1)

# Hardcoded Rooms
df_rooms = pd.read_csv('rooms.csv')

# ==========================================
# 2. PRE-PROCESSING
# ==========================================
print("Preprocessing Constraints...")

# Instructor Map
instructor_map = {} 
for idx, row in df_courses.iterrows():
    cid = row['course_id']
    instructors = [row['instructor1'], row['instructor2']]
    for inst in instructors:
        if pd.notna(inst):
            if inst not in instructor_map: instructor_map[inst] = []
            instructor_map[inst].append(cid)

# Student Conflicts
student_clashes = set() 
student_groups = df_students.groupby('student_id')['course_id'].apply(list)
for _, taken in student_groups.items():
    taken = sorted(list(set(taken))) 
    for i in range(len(taken)):
        for j in range(i + 1, len(taken)):
            student_clashes.add((taken[i], taken[j]))

enrollment = df_students.groupby('course_id').size().to_dict()

days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
slots_per_day = 6 
time_slots = [f"{d}_{s+1}" for d in days for s in range(slots_per_day)]

# Slot Weights (Time Penalty)
slot_weights = {}
for t in time_slots:
    day, num = t.split('_')
    slot_weights[t] = (int(num) - 1) * W1_TIME_PENALTY

# ==========================================
# 3. BUILD MODEL
# ==========================================
print("Building MILP Model with Objectives...")
prob = pulp.LpProblem("OptiTime_Advanced", pulp.LpMinimize)

course_ids = df_courses['course_id'].tolist()
room_ids = df_rooms['room'].tolist()

# --- VARIABLES ---
x = {} 
for c in course_ids:
    req = enrollment.get(c, 0)
    for t in time_slots:
        for r in room_ids:
            r_cap = df_rooms.loc[df_rooms['room'] == r, 'capacity'].values[0]
            if r_cap >= req:
                is_lab = 'Lab' in str(df_courses.loc[df_courses['course_id']==c, 'title'].values[0])
                is_lab_room = 'R-' in r
                if is_lab != is_lab_room: continue
                x[(c, t, r)] = pulp.LpVariable(f"x_{c}_{t}_{r}", cat='Binary')

# --- HARD CONSTRAINTS ---
print("Adding Hard Constraints...")

# Slot Requirements
for idx, row in df_courses.iterrows():
    c = row['course_id']
    prob += pulp.lpSum([x.get((c, t, r), 0) for t in time_slots for r in room_ids]) == row['slots_required']

# Room Conflict
for t in time_slots:
    for r in room_ids:
        prob += pulp.lpSum([x.get((c, t, r), 0) for c in course_ids]) <= 1

# Instructor Conflict
for inst, c_list in instructor_map.items():
    for t in time_slots:
        prob += pulp.lpSum([x.get((c, t, r), 0) for c in c_list for r in room_ids]) <= 1

# Student Clashes
for (c1, c2) in student_clashes:
    for t in time_slots:
        c1_vars = [x[(c1, t, r)] for r in room_ids if (c1, t, r) in x]
        c2_vars = [x[(c2, t, r)] for r in room_ids if (c2, t, r) in x]
        if c1_vars and c2_vars:
            prob += pulp.lpSum(c1_vars) + pulp.lpSum(c2_vars) <= 1

# --- SOFT CONSTRAINTS ---
print("Adding Objective Functions...")

# Term 1: Late Slots
obj_time = pulp.lpSum([x[key] * slot_weights[key[1]] for key in x])

# Term 2: Prof Overload
overload_vars = []
for inst, c_list in instructor_map.items():
    if inst == 'TBD': continue 
    for d in days:
        day_slots = [s for s in time_slots if s.startswith(d)]
        daily_load = pulp.lpSum([x.get((c, t, r), 0) for c in c_list for t in day_slots for r in room_ids])
        excess = pulp.LpVariable(f"excess_{inst}_{d}", lowBound=0)
        prob += daily_load <= PROF_DAILY_LIMIT + excess
        overload_vars.append(excess)

prob += obj_time + (W2_PROF_OVERLOAD * pulp.lpSum(overload_vars))

# ==========================================
# 4. SOLVE (WITH TIME LIMIT)
# ==========================================
print(f"Solving with {SOLVER_TIME_LIMIT}s time limit...")

# --- CRITICAL CHANGE HERE ---
# We use PULP_CBC_CMD to pass specific arguments to the solver binary
# timeLimit: Max seconds to run
# gapRel: Stop if the solution is within 5% (0.05) of the mathematical optimum
solver = pulp.PULP_CBC_CMD(msg=True, timeLimit=SOLVER_TIME_LIMIT, gapRel=0.05)
prob.solve(solver)

status = pulp.LpStatus[prob.status]
print(f"Status: {status}")

# ==========================================
# 5. EXPORT
# ==========================================
if status in ['Optimal', 'Feasible']: # Note: Status might be 'Feasible' if time ran out but solution exists
    results = []
    for (c, t, r), var in x.items():
        if var.varValue == 1:
            day, slot_num = t.split('_')
            course_row = df_courses[df_courses['course_id'] == c]
            course_name = course_row['title'].values[0] if not course_row.empty else c
            results.append({
                'Day': day, 'Slot': int(slot_num), 'Course': c, 'Room': r, 'Title': course_name
            })
            
    with open('timetable_output.json', 'w') as f:
        json.dump(results, f, indent=4)
    print(f"Success! Saved solution (Objective: {pulp.value(prob.objective)})")
else:
    print("No feasible solution found within the time limit.")