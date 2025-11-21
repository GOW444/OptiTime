import pandas as pd
import pulp
import json
from io import StringIO
import sys

# ==========================================
# 1. LOAD DATA 
# ==========================================

print("Loading Data...")

# A. Courses (External CSV)
try:
    df_courses = pd.read_csv('courses.csv')
    print(f"Loaded {len(df_courses)} courses from 'courses.csv'.")
except FileNotFoundError:
    print("Error: 'courses.csv' not found. Please ensure the file is in the same directory.")
    sys.exit(1)

# B. Students (External CSV - NEW DATASET)
try:
    df_students = pd.read_csv('student_data_large.csv')
    print(f"Loaded {len(df_students)} student records from 'student_data_large.csv'.")
except FileNotFoundError:
    print("Error: 'student_data_large.csv' not found.")
    sys.exit(1)

# C. Rooms 
rooms_csv = """room,capacity
A307,140
A106,135
A304,135
P201,140
P202,140
R110,100
A317,130
R-106,120
R-107,120
R-108,120"""
df_rooms = pd.read_csv(StringIO(rooms_csv))
print(f"Loaded {len(df_rooms)} rooms.")

# ==========================================
# 2. PRE-PROCESSING
# ==========================================

print("Preprocessing Constraints...")

# A. Calculate Enrollments vs Room Capacity
enrollment_counts = df_students.groupby('course_id').size().to_dict()

# B. Map Instructors to Courses
instructor_map = {} 
for idx, row in df_courses.iterrows():
    cid = row['course_id']
    instructors = [row['instructor1'], row['instructor2']]
    for inst in instructors:
        if pd.notna(inst):
            if inst not in instructor_map: instructor_map[inst] = []
            instructor_map[inst].append(cid)

# C. Build Student Conflict Matrix
# This ensures that if a student takes Course A and Course B, they aren't scheduled at the same time.
student_clashes = set() 
student_groups = df_students.groupby('student_id')['course_id'].apply(list)

for _, taken_courses in student_groups.items():
    # Sort courses to avoid duplicate pairs like (C1, C2) and (C2, C1)
    taken_courses = sorted(taken_courses)
    for i in range(len(taken_courses)):
        for j in range(i + 1, len(taken_courses)):
            c1 = taken_courses[i]
            c2 = taken_courses[j]
            student_clashes.add((c1, c2))

print(f"Identified {len(student_clashes)} course pairs that share students (Clash Constraints).")

# D. Define Time Slots (Mon-Fri, 6 slots/day)
days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
slots_per_day = 6 
time_slots = [f"{d}_{s+1}" for d in days for s in range(slots_per_day)]

# ==========================================
# 3. BUILD THE PULP MODEL
# ==========================================

print("Building MILP Model...")
prob = pulp.LpProblem("OptiTime_Large_Scheduler", pulp.LpMinimize)

course_ids = df_courses['course_id'].tolist()
room_ids = df_rooms['room'].tolist()

# --- VARIABLES ---
# x[c, t, r] = 1 if course c is at time t in room r
x = {}
vars_count = 0

for c in course_ids:
    req_enrollment = enrollment_counts.get(c, 0)
    for t in time_slots:
        for r in room_ids:
            # 1. Capacity Constraint (Hard Filtering)
            r_cap = df_rooms.loc[df_rooms['room'] == r, 'capacity'].values[0]
            if r_cap >= req_enrollment:
                
                # 2. Lab vs Lecture Room Constraint
                is_lab = 'Lab' in str(df_courses.loc[df_courses['course_id']==c, 'title'].values[0])
                is_lab_room = 'R-' in r
                
                if is_lab and not is_lab_room: continue
                if not is_lab and is_lab_room: continue
                    
                x[(c, t, r)] = pulp.LpVariable(f"x_{c}_{t}_{r}", cat='Binary')
                vars_count += 1

print(f"Created {vars_count} binary variables.")

# --- CONSTRAINTS ---

# 1. Slot Requirement: Each course must be scheduled exactly h_c times
for idx, row in df_courses.iterrows():
    c = row['course_id']
    required = row['slots_required']
    prob += pulp.lpSum([x.get((c, t, r), 0) for t in time_slots for r in room_ids]) == required, f"Req_Slots_{c}"

# 2. Room Conflict: Max 1 course per room per time slot
for t in time_slots:
    for r in room_ids:
        prob += pulp.lpSum([x.get((c, t, r), 0) for c in course_ids]) <= 1, f"Room_Conflict_{r}_{t}"

# 3. Instructor Conflict: Max 1 course per instructor per time slot
for inst, c_list in instructor_map.items():
    for t in time_slots:
        prob += pulp.lpSum([x.get((c, t, r), 0) for c in c_list for r in room_ids]) <= 1, f"Inst_Conflict_{inst}_{t}"

# 4. Student Clash: Courses sharing students cannot be at the same time
# Optimizing: Only check if both c1 and c2 have variables for this time t
for (c1, c2) in student_clashes:
    for t in time_slots:
        # Get all room options for c1 at time t
        c1_vars = [x[(c1, t, r)] for r in room_ids if (c1, t, r) in x]
        # Get all room options for c2 at time t
        c2_vars = [x[(c2, t, r)] for r in room_ids if (c2, t, r) in x]
        
        # Only add constraint if both courses *could* be scheduled at t
        if c1_vars and c2_vars:
            prob += pulp.lpSum(c1_vars) + pulp.lpSum(c2_vars) <= 1, f"Stud_Clash_{c1}_{c2}_{t}"

# Objective: Feasibility Only (0)
prob += 0, "Feasibility_Only"

# ==========================================
# 4. SOLVE
# ==========================================

print("Solving... (This may take longer due to larger dataset)")
# Using default CBC solver
prob.solve()

status = pulp.LpStatus[prob.status]
print(f"Solver Status: {status}")

# ==========================================
# 5. OUTPUT & EXPORT
# ==========================================

if status == 'Optimal':
    results = []
    
    for (c, t, r), var in x.items():
        if var.varValue == 1:
            day, slot_num = t.split('_')
            
            course_row = df_courses[df_courses['course_id'] == c]
            course_name = course_row['title'].values[0] if not course_row.empty else c
            
            entry = f"{c} ({r})"
            
            results.append({
                'Day': day, 
                'Slot': int(slot_num), 
                'Course': c, 
                'Room': r, 
                'Title': course_name,
                'Display': entry
            })
            
    # Export to JSON
    output_filename = 'new_timetable_output.json'
    with open(output_filename, 'w') as f:
        json.dump(results, f, indent=4)
    print(f"\n[SUCCESS] Timetable generated and saved to {output_filename}")
    
    # Print simple grid
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        df_pivot = df_res.pivot_table(index='Slot', columns='Day', values='Display', aggfunc=lambda x: ' '.join(x))
        cols = [d for d in days if d in df_pivot.columns]
        print("\nGenerated Schedule:")
        print(df_pivot[cols].fillna(''))
    else:
        print("Warning: Optimal status returned but no classes scheduled.")
else:
    print("Could not find a feasible solution.")
    print("Tips: Check if room capacities are large enough for the new student counts.")