# generate_all_data.py
# Writes:
#  - student_data_large.csv
#  - courses.csv
#  - rooms.csv


import csv
import random
from pathlib import Path

OUT = Path('.')  

# -------------------------
# Student data generation
# -------------------------
filename = OUT / "student_data_large.csv"

first_names = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayan", "Krishna",
    "Ishaan", "Diya", "Saanvi", "Ananya", "Aadhya", "Kiara", "Ira", "Nisha", "Riya",
    "Pooja", "Neha", "Ishika", "Simran", "Ritika", "Shruti", "Karan", "Rohan", "Manav"
]
last_names = [
    "Sharma", "Verma", "Patel", "Iyer", "Reddy", "Nair", "Mehta", "Singh", "Gupta",
    "Malhotra", "Bhat", "Saxena", "Deshmukh", "Jha", "Kaur", "Rao", "Joshi", "Das"
]

def get_random_name():
    return f"{random.choice(first_names)} {random.choice(last_names)}"

# Course groups
group_a_courses = ["C1", "C2", "C3", "C17"]    # 60 students, exact same courses
group_b_courses = ["C4", "C5", "C6"]           # 30 students, exact same courses
elective_pool = ["C7", "C8", "C9", "C10", "C11", "C12", "C13", "C14", "C15", "C16"]

data_rows = []

# GENERATE GROUP A (60 Students - High Overlap)
# IDs: BT202501001 ... BT202501060
for i in range(1, 61):
    student_id = f"BT202501{i:03d}"
    name = get_random_name()
    for course in group_a_courses:
        data_rows.append([student_id, name, course])

# GENERATE GROUP B (30 Students - Medium Overlap)
# IDs: IMT202501001 ... IMT202501030
for i in range(1, 31):
    student_id = f"IMT202501{i:03d}"
    name = get_random_name()
    for course in group_b_courses:
        data_rows.append([student_id, name, course])

# GENERATE GROUP C (20 Students - Random/No Overlap)
# IDs: BT202502001 ... BT202502020
for i in range(1, 21):
    student_id = f"BT202502{i:03d}"
    name = get_random_name()
    num_courses = random.randint(3, 4)
    random_courses = random.sample(elective_pool, num_courses)
    for course in random_courses:
        data_rows.append([student_id, name, course])

# Write student CSV
with open(filename, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["student_id", "student_name", "course_id"])
    writer.writerows(data_rows)

print(f"Successfully generated {len(data_rows)} rows in '{filename.name}'")

# -------------------------
# Courses and Rooms files
# -------------------------
courses = [
    ("C1","AIM 101-Statistics for DS",4,"Vaishnavi Gujjala","","A307","Btech DSAI-2025",4),
    ("C2","AIM 102-Statistical Machine Learning",4,"Aswin Kannan","","A307","Btech DSAI-2025",4),
    ("C3","DAS 101-Database Systems-Sec-B",4,"Uttam Kumar","","A307","Btech DSAI-2025",4),
    ("C4","DAS 101P-Database Systems Lab-Sec-B",4,"Vinu Venugopal","","A307","Btech DSAI-2025",4),
    ("C5","CSE 102-Data Structures and Algorithms-Sec-B",4,"Amit Chotopadhyaya","","A307","BTech DSAI 2025+BTech ECE iMTech ECE-2025",4),
    ("C6","CSE 102-Data Structures and Algorithms-Sec-A",4,"Muralidhara V N","","A106","BTech CSE + iMTech CSE-2025",4),
    ("C7","CSE 102P-DSA Lab-Sec-A",4,"Muralidhara V N","","R-106,107,108","BTech CSE + iMTech CSE-2025",4),
    ("C8","CSE 102P-DSA Lab-Sec-B",4,"Saumya Shankar","","R-106,107,108","BTech DSAI 2025 + BTech ECE iMTech ECE-2025",4),
    ("C9","EGC 121-Computer Architecture-Sec-A",4,"TBD","","A106","BTech CSE - 2025",4),
    ("C10","EGC 121-Computer Architecture-Sec-B",4,"TBD","","A304","iMTech CSE + BTech ECE iMTech ECE-2025",4),
    ("C11","EGC 123-Computer Networks-Sec-A",4,"Ajay Bakre","","A106","BTech CSE - 2025",4),
    ("C12","EGC 123-Computer Networks-Sec-B",4,"Badrinath R","","A304","iMTech CSE + BTech ECE iMTech ECE-2025",4),
    ("C13","DHS 101B-Economics II-Sec-A",2,"Amit Prakash","","A106","BTech CSE + iMTech CSE-2025",2),
    ("C14","DHS 101B-Economics II-Sec-B",2,"Amit Prakash","","A307","BTech DSAI + BTech ECE + iMTech ECE-2025",2),
    ("C15","AMS 103-Calculus-Sec-A",4,"Manisha Kulkarni","","A106","BTech CSE + iMTech CSE-2025",4),
    ("C16","AMS 103-Calculus-Sec-B",4,"Sanghasri Mukhopadhyay","","A307","BTech DSAI + BTech ECE iMTech ECE-2025",4),
    ("C17","Physical Education",0,"Neha Arora","","","All Batches",3)
]

rooms = [
    ("A307",140),
    ("A106",135),
    ("A304",135),
    ("P201",140),
    ("P202",140),
    ("R110",100),
    ("A317",130),
    ("R-106",120),
    ("R-107",120),
    ("R-108",120)
]

# courses.csv
with open(OUT / 'courses.csv','w', newline='', encoding='utf8') as f:
    writer = csv.writer(f)
    writer.writerow(['course_id','title','credits','instructor1','instructor2','room','batches','slots_required'])
    writer.writerows(courses)

# rooms.csv
with open(OUT / 'rooms.csv','w', newline='', encoding='utf8') as f:
    writer = csv.writer(f)
    writer.writerow(['room','capacity'])
    writer.writerows(rooms)

print("Created courses.csv and rooms.csv in the current directory")
