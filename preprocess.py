# preprocess.py
# Produces conflict_matrix.json and allowed_rooms.json
import pandas as pd
import json
from collections import defaultdict
from pathlib import Path
DATA = Path('data')

courses = pd.read_csv(DATA/'courses.csv')
rooms = pd.read_csv(DATA/'rooms.csv')
enroll = pd.read_csv(DATA/'enrollments.csv')

# conflict matrix: if any student appears in both courses -> conflict
students = enroll.groupby('student_id')['course_id'].apply(list).to_dict()
conflict = defaultdict(dict)
for st, clist in students.items():
    for i in range(len(clist)):
        for j in range(i+1, len(clist)):
            c1, c2 = clist[i], clist[j]
            conflict.setdefault(c1, {})[c2] = 1
            conflict.setdefault(c2, {})[c1] = 1

# allowed rooms by capacity (room capacity >= enrollment of course)
enrollment_by_course = courses.set_index('course_id')['slots_required']  # we will use slots_required for model; enrollment we don't have exact counts -> approximate
# But we have no per-course enrolment numbers here. For simplicity, we estimate enrollment from enrollments.csv
course_counts = enroll['course_id'].value_counts().to_dict()
allowed = {}
for _, row in courses.iterrows():
    c = row['course_id']
    need = course_counts.get(c, 0)
    # default: if no students listed, allow all rooms
    allowed[c] = []
    for _, r in rooms.iterrows():
        if need == 0 or r['capacity'] >= need:
            allowed[c].append(r['room'])

# save
Path('data').mkdir(parents=True, exist_ok=True)
with open(DATA/'conflict_matrix.json','w',encoding='utf8') as f:
    json.dump(conflict, f, indent=2)
with open(DATA/'allowed_rooms.json','w',encoding='utf8') as f:
    json.dump(allowed, f, indent=2)

print("Wrote data/conflict_matrix.json and data/allowed_rooms.json")
