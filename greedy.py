# greedy.py
# Simple greedy scheduler: assign courses one by one into first available slot+room without conflicts
import pandas as pd
from pathlib import Path
RESULTS = Path('results'); RESULTS.mkdir(exist_ok=True)
DATA = Path('data')

def run_greedy():
    courses = pd.read_csv(DATA/'courses.csv')
    rooms = pd.read_csv(DATA/'rooms.csv')
    enroll = pd.read_csv(DATA/'enrollments.csv')

    C = list(courses['course_id'])
    R = list(rooms['room'])
    T = [f't{t}' for t in range(1,11)]

    h = {row['course_id']: int(row['slots_required']) for _, row in courses.iterrows()}
    course_students = enroll.groupby('course_id')['student_id'].apply(list).to_dict()

    # allowed rooms by capacity
    course_counts = enroll['course_id'].value_counts().to_dict()
    allowed = {}
    for _, row in courses.iterrows():
        c = row['course_id']; need = course_counts.get(c,0)
        allowed[c] = [r for _, rcap in rooms.iterrows() for r in [rooms.loc[_,'room']] if (need==0 or rooms.loc[_,'capacity'] >= need)]
        # simpler: use all rooms with capacity >= need
        allowed[c] = [r for r,cap in zip(rooms['room'], rooms['capacity']) if need==0 or cap>=need]

    room_busy = { (t,r): False for t in T for r in R }
    student_busy = { s: set() for s in enroll['student_id'].unique() }

    assignments = []
    # order courses by descending enrollment
    order = sorted(C, key=lambda c: course_counts.get(c,0), reverse=True)
    for c in order:
        needed = h[c]
        assigned = 0
        for t in T:
            if assigned >= needed:
                break
            for r in allowed[c]:
                if room_busy[(t,r)]: continue
                # check student conflicts
                conflict = False
                for s in course_students.get(c, []):
                    if t in student_busy.get(s, set()):
                        conflict = True; break
                if conflict: continue
                # assign
                room_busy[(t,r)] = True
                for s in course_students.get(c, []):
                    student_busy[s].add(t)
                assignments.append({'course_id': c, 'timeslot': t, 'room': r})
                assigned += 1
                break
        # if not fully assigned, leave partial (we'll report)
    df = pd.DataFrame(assignments)
    df.to_csv(RESULTS/'assignments_greedy.csv', index=False)

    # metrics
    total_assigned = len(df)
    course_assign_counts = df.groupby('course_id').size().to_dict()
    courses_fully_assigned = sum(1 for c in C if course_assign_counts.get(c,0) >= h[c])
    # simple room utilization
    caps = dict(zip(rooms['room'], rooms['capacity']))
    total_assigned_seats = sum(enroll['course_id'].value_counts().get(row['course_id'],0) for _,row in df.iterrows())
    total_capacity_used = sum(caps.get(row['room'],0) for _,row in df.iterrows())
    util = round(100 * total_assigned_seats / total_capacity_used, 2) if total_capacity_used>0 else 0.0
    metrics = {
        'num_assignments': int(total_assigned),
        'courses_fully_assigned': int(courses_fully_assigned),
        'total_courses': len(C),
        'room_util_percent': util
    }
    import json
    with open(RESULTS/'metrics_greedy.json','w') as f:
        json.dump(metrics, f, indent=2)
    print("Greedy finished. Saved assignments_greedy.csv and metrics_greedy.json")
    return df, metrics

if __name__ == '__main__':
    run_greedy()
