
# Creates data/courses.csv, data/rooms.csv, data/enrollments.csv
import csv
from pathlib import Path

OUT = Path('data')
OUT.mkdir(exist_ok=True)

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
    ("A307",40),
    ("A106",35),
    ("A304",35),
    ("P201",40),
    ("P202",40),
    ("R110",30),
    ("A317",30),
    ("R-106",20),
    ("R-107",20),
    ("R-108",20)
]

enrollments = [
("BT202501001","Aarav Sharma","C1"),
("BT202501001","Aarav Sharma","C2"),
("BT202501001","Aarav Sharma","C5"),
("BT202501001","Aarav Sharma","C15"),
("BT202501002","Ishika Reddy","C1"),
("BT202501002","Ishika Reddy","C3"),
("BT202501002","Ishika Reddy","C6"),
("BT202501002","Ishika Reddy","C11"),
("BT202501003","Karan Mehta","C2"),
("BT202501003","Karan Mehta","C4"),
("BT202501003","Karan Mehta","C8"),
("BT202501003","Karan Mehta","C16"),
("BT202501004","Diya Nair","C5"),
("BT202501004","Diya Nair","C7"),
("BT202501004","Diya Nair","C12"),
("BT202501004","Diya Nair","C15"),
("BT202501005","Rohan Patel","C1"),
("BT202501005","Rohan Patel","C9"),
("BT202501005","Rohan Patel","C11"),
("BT202501005","Rohan Patel","C13"),
("BT202501006","Nisha Verma","C2"),
("BT202501006","Nisha Verma","C10"),
("BT202501006","Nisha Verma","C14"),
("BT202501006","Nisha Verma","C16"),
("BT202501007","Aditya Iyer","C3"),
("BT202501007","Aditya Iyer","C4"),
("BT202501007","Aditya Iyer","C5"),
("BT202501007","Aditya Iyer","C11"),
("BT202501008","Saanvi Gupta","C6"),
("BT202501008","Saanvi Gupta","C7"),
("BT202501008","Saanvi Gupta","C12"),
("BT202501008","Saanvi Gupta","C15"),
("BT202501009","Manav Deshmukh","C1"),
("BT202501009","Manav Deshmukh","C3"),
("BT202501009","Manav Deshmukh","C16"),
("BT202501009","Manav Deshmukh","C14"),
("BT202501010","Ananya Jha","C5"),
("BT202501010","Ananya Jha","C8"),
("BT202501010","Ananya Jha","C11"),
("BT202501010","Ananya Jha","C12"),
("BT202502001","Harsh Vardhan","C1"),
("BT202502001","Harsh Vardhan","C2"),
("BT202502001","Harsh Vardhan","C5"),
("BT202502002","Simran Kaur","C2"),
("BT202502002","Simran Kaur","C4"),
("BT202502002","Simran Kaur","C8"),
("BT202502003","Pranav Rao","C3"),
("BT202502003","Pranav Rao","C11"),
("BT202502003","Pranav Rao","C14"),
("BT202502004","Aditi Joshi","C6"),
("BT202502004","Aditi Joshi","C15"),
("BT202502004","Aditi Joshi","C12"),
("BT202502005","Krish Malhotra","C1"),
("BT202502005","Krish Malhotra","C3"),
("BT202502005","Krish Malhotra","C5"),
("BT202502006","Ira Narayan","C2"),
("BT202502006","Ira Narayan","C9"),
("BT202502006","Ira Narayan","C13"),
("BT202502007","Dev Goyal","C5"),
("BT202502007","Dev Goyal","C7"),
("BT202502007","Dev Goyal","C12"),
("BT202502008","Shruti Menon","C6"),
("BT202502008","Shruti Menon","C10"),
("BT202502008","Shruti Menon","C16"),
("IMT202501001","Aishwarya Menon","C6"),
("IMT202501001","Aishwarya Menon","C15"),
("IMT202501001","Aishwarya Menon","C12"),
("IMT202501002","Neel Kolhe","C7"),
("IMT202501002","Neel Kolhe","C8"),
("IMT202501002","Neel Kolhe","C5"),
("IMT202501003","Vishal Singh","C1"),
("IMT202501003","Vishal Singh","C9"),
("IMT202501003","Vishal Singh","C11"),
("IMT202501004","Ritika Shah","C2"),
("IMT202501004","Ritika Shah","C10"),
("IMT202501004","Ritika Shah","C14"),
("IMT202501005","Akash Das","C3"),
("IMT202501005","Akash Das","C11"),
("IMT202501005","Akash Das","C16"),
]

# write files
with open(OUT/'courses.csv','w',newline='',encoding='utf8') as f:
    writer = csv.writer(f)
    writer.writerow(['course_id','title','credits','instructor1','instructor2','room','batches','slots_required'])
    writer.writerows(courses)

with open(OUT/'rooms.csv','w',newline='',encoding='utf8') as f:
    writer = csv.writer(f)
    writer.writerow(['room','capacity'])
    writer.writerows(rooms)

with open(OUT/'enrollments.csv','w',newline='',encoding='utf8') as f:
    writer = csv.writer(f)
    writer.writerow(['student_id','student_name','course_id'])
    writer.writerows(enrollments)

print("Created data/courses.csv, data/rooms.csv, data/enrollments.csv")