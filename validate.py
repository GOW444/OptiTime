# validate.py
# Validate assignments CSV for student conflicts and professor conflicts (basic)
import pandas as pd
from pathlib import Path
DATA = Path('data')
RESULTS = Path('results')

def validate(assignments_csv='results/assignments_milp.csv'):
    assign = pd.read_csv(assignments_csv)
    enroll = pd.read_csv(DATA/'enrollments.csv')
    courses = pd.read_csv(DATA/'courses.csv')

    # build mapping course->timeslots
    course_times = assign.groupby('course_id')['timeslot'].apply(list).to_dict()

    # check student conflicts
    student_conflicts = 0
    for student, group in enroll.groupby('student_id'):
        times = {}
        for _, row in group.iterrows():
            c = row['course_id']
            for t in course_times.get(c, []):
                times[t] = times.get(t,0) + 1
        for t,cnt in times.items():
            if cnt>1: student_conflicts += (cnt-1)

    print(f"Student conflicts found: {student_conflicts}")

    # professor conflicts (if instructor teaches multiple courses)
    instr_map = courses.set_index('course_id')['instructor1'].to_dict()
    # invert instructor -> courses
    instr_courses = {}
    for c, instr in instr_map.items():
        instr_courses.setdefault(instr, []).append(c)
    prof_conflicts = 0
    for instr, clist in instr_courses.items():
        if instr == 'TBD' or pd.isna(instr) or instr.strip()=='':
            continue
        # check pairwise
        for i in range(len(clist)):
            for j in range(i+1, len(clist)):
                c1, c2 = clist[i], clist[j]
                for t in course_times.get(c1, []):
                    if t in course_times.get(c2, []):
                        prof_conflicts += 1
    print(f"Professor conflicts found (counting overlaps): {prof_conflicts}")

if __name__ == '__main__':
    validate('results/assignments_milp.csv')
    # also validate greedy
    validate('results/assignments_greedy.csv')
