import pandas as pd
import json
import sys

# ==========================================
# 1. CONFIGURATION & LOADING
# ==========================================
def load_data():
    print("Loading Data for Validation...")
    try:
        df_courses = pd.read_csv('courses.csv')
        df_students = pd.read_csv('student_data_large.csv')
        with open('timetable_output.json', 'r') as f:
            schedule_data = json.load(f)
        df_schedule = pd.DataFrame(schedule_data)
        print("✅ Data Loaded Successfully.")
        return df_courses, df_students, df_schedule
    except FileNotFoundError as e:
        print(f"❌ CRITICAL ERROR: Missing file - {e}")
        sys.exit(1)

def validate_schedule(df_courses, df_students, df_schedule):
    error_count = 0
    warning_count = 0
    
    print("\n" + "="*50)
    print("🔍 STARTING AUDIT")
    print("="*50)

    # ==========================================
    # CHECK 1: COURSE SLOT REQUIREMENTS
    # ==========================================
    print("\n[1] Checking Course Slot Requirements...")
    
    # Map Course ID -> Required Slots
    req_slots = df_courses.set_index('course_id')['slots_required'].to_dict()
    
    # Count actual slots in generated schedule
    actual_slots = df_schedule['Course'].value_counts().to_dict()
    
    slot_errors = []
    for cid, required in req_slots.items():
        actual = actual_slots.get(cid, 0)
        if actual != required:
            slot_errors.append(f"   🔴 {cid}: Required {required}, Got {actual}")
            error_count += 1
            
    if not slot_errors:
        print("   ✅ PASS: All courses met slot requirements.")
    else:
        print("   ❌ FAIL: Mismatches found:")
        for e in slot_errors: print(e)

    # ==========================================
    # CHECK 2: STUDENT CLASHES
    # ==========================================
    print("\n[2] Checking Student Clashes (This may take a moment)...")
    
    # Optimization: Create a lookup for when courses are happening
    # Structure: course_id -> list of (Day, Slot) tuples
    course_timing = {}
    for _, row in df_schedule.iterrows():
        c = row['Course']
        time_key = (row['Day'], row['Slot'])
        if c not in course_timing: course_timing[c] = []
        course_timing[c].append(time_key)

    # Group students by ID and get their course list
    student_groups = df_students.groupby('student_id')['course_id'].apply(list)
    
    clash_list = []
    
    for student_id, courses in student_groups.items():
        # Find all time slots this student is busy
        busy_slots = []
        for c in courses:
            if c in course_timing:
                busy_slots.extend(course_timing[c])
        
        # Check for duplicates in busy_slots
        # If (Mon, 1) appears twice, the student is in two places at once
        seen = set()
        duplicates = set()
        for slot in busy_slots:
            if slot in seen:
                duplicates.add(slot)
            else:
                seen.add(slot)
        
        if duplicates:
            clash_list.append(f"   🔴 Student {student_id} has clash at {list(duplicates)}")
            error_count += 1

    if not clash_list:
        print(f"   ✅ PASS: Checked {len(student_groups)} students. Zero clashes found.")
    else:
        print(f"   ❌ FAIL: Found {len(clash_list)} students with clashes.")
        # Print first 5 only to avoid spamming console
        for c in clash_list[:5]: print(c)
        if len(clash_list) > 5: print(f"   ... and {len(clash_list)-5} more.")

    # ==========================================
    # CHECK 3: PROFESSOR WORKLOAD (Soft Constraint)
    # ==========================================
    print("\n[3] Analyzing Professor Workload (Soft Constraint)...")
    
    # Build Instructor Map
    inst_schedule = []
    for idx, row in df_courses.iterrows():
        instructors = [row['instructor1'], row['instructor2']]
        for inst in instructors:
            if pd.notna(inst) and inst != 'TBD':
                # Get slots for this course
                course_slots = df_schedule[df_schedule['Course'] == row['course_id']]
                for _, s_row in course_slots.iterrows():
                    inst_schedule.append({'Instructor': inst, 'Day': s_row['Day'], 'Slot': s_row['Slot']})
    
    df_inst = pd.DataFrame(inst_schedule)
    
    if not df_inst.empty:
        # Count hours per day per instructor
        daily_load = df_inst.groupby(['Instructor', 'Day']).size()
        
        # Check against limit (2 slots per day)
        overloaded = daily_load[daily_load > 2]
        
        if overloaded.empty:
            print("   ✅ EXCELLENT: No professor teaches more than 2 slots/day.")
        else:
            print(f"   ⚠️  INFO: {len(overloaded)} instances of high workload (>2 slots/day).")
            print("   (This is allowed in the soft-constraint model, but worth noting)")
            for idx, count in overloaded.items():
                print(f"      - {idx[0]} on {idx[1]}: {count} slots")
                warning_count += 1
    else:
        print("   ⚠️  No instructor data found assigned to scheduled courses.")

    # ==========================================
    # SUMMARY
    # ==========================================
    print("\n" + "="*50)
    if error_count == 0:
        print("✅ RESULT: VALID TIMETABLE")
        print("System represents a feasible solution.")
    else:
        print(f"❌ RESULT: INVALID ({error_count} Critical Errors)")
    print("="*50 + "\n")

if __name__ == "__main__":
    courses, students, schedule = load_data()
    validate_schedule(courses, students, schedule)
