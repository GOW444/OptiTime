import csv
import random

# --- CONFIGURATION ---
filename = "student_data_large.csv"

# 1. Data Pools for Random Name Generation
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

# 2. Define Course Groups
# Group A: 60 Students with EXACT SAME courses (e.g., 1st Year Core)
group_a_courses = ["C1", "C2", "C3", "C17"] 

# Group B: 30 Students with ANOTHER set of same courses (e.g., 2nd Year Stream)
group_b_courses = ["C4", "C5", "C6"]

# Group C: Random pool of electives for the remaining students
elective_pool = ["C7", "C8", "C9", "C10", "C11", "C12", "C13", "C14", "C15", "C16"]

# --- GENERATION LOGIC ---
data_rows = []

# GENERATE GROUP A (60 Students - High Overlap)
for i in range(1, 61):
    student_id = f"BT2025{i:03d}" # Generates BT202501001 to ...060
    name = get_random_name()
    for course in group_a_courses:
        data_rows.append([student_id, name, course])

# GENERATE GROUP B (30 Students - Medium Overlap)
for i in range(1, 31):
    student_id = f"IMT202501{i:03d}" # Generates IMT202501001 to ...030
    name = get_random_name()
    for course in group_b_courses:
        data_rows.append([student_id, name, course])

# GENERATE GROUP C (20 Students - Random/No Overlap)
for i in range(1, 21):
    student_id = f"BT202502{i:03d}" # Generates BT202502001 to ...020
    name = get_random_name()
    # Pick 3 to 4 random courses from the elective pool
    num_courses = random.randint(3, 4)
    random_courses = random.sample(elective_pool, num_courses)
    for course in random_courses:
        data_rows.append([student_id, name, course])

# --- WRITE TO CSV ---
header = ["student_id", "student_name", "course_id"]

with open(filename, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(data_rows)

print(f"Successfully generated {len(data_rows)} rows of data in '{filename}'")