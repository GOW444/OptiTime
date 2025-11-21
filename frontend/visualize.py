import streamlit as st
import pandas as pd
import json
from io import StringIO
import sys

# ==========================================
# 1. DATA SETUP
# ==========================================

#hardcoded input ,read from enrollments.csv later
STUDENTS_CSV_CONTENT = """student_id,student_name,course_id
BT202501001,Aarav Sharma,C1
BT202501001,Aarav Sharma,C2
BT202501001,Aarav Sharma,C5
BT202501001,Aarav Sharma,C15
BT202501002,Ishika Reddy,C1
BT202501002,Ishika Reddy,C3
BT202501002,Ishika Reddy,C6
BT202501002,Ishika Reddy,C11
BT202501003,Karan Mehta,C2
BT202501003,Karan Mehta,C4
BT202501003,Karan Mehta,C8
BT202501003,Karan Mehta,C16
BT202501004,Diya Nair,C5
BT202501004,Diya Nair,C7
BT202501004,Diya Nair,C12
BT202501004,Diya Nair,C15
BT202501005,Rohan Patel,C1
BT202501005,Rohan Patel,C9
BT202501005,Rohan Patel,C11
BT202501005,Rohan Patel,C13
BT202501006,Nisha Verma,C2
BT202501006,Nisha Verma,C10
BT202501006,Nisha Verma,C14
BT202501006,Nisha Verma,C16
BT202501007,Aditya Iyer,C3
BT202501007,Aditya Iyer,C4
BT202501007,Aditya Iyer,C5
BT202501007,Aditya Iyer,C11
BT202501008,Saanvi Gupta,C6
BT202501008,Saanvi Gupta,C7
BT202501008,Saanvi Gupta,C12
BT202501008,Saanvi Gupta,C15
BT202501009,Manav Deshmukh,C1
BT202501009,Manav Deshmukh,C3
BT202501009,Manav Deshmukh,C16
BT202501009,Manav Deshmukh,C14
BT202501010,Ananya Jha,C5
BT202501010,Ananya Jha,C8
BT202501010,Ananya Jha,C11
BT202501010,Ananya Jha,C12
BT202502001,Harsh Vardhan,C1
BT202502001,Harsh Vardhan,C2
BT202502001,Harsh Vardhan,C5
BT202502002,Simran Kaur,C2
BT202502002,Simran Kaur,C4
BT202502002,Simran Kaur,C8
BT202502003,Pranav Rao,C3
BT202502003,Pranav Rao,C11
BT202502003,Pranav Rao,C14
BT202502004,Aditi Joshi,C6
BT202502004,Aditi Joshi,C15
BT202502004,Aditi Joshi,C12
BT202502005,Krish Malhotra,C1
BT202502005,Krish Malhotra,C3
BT202502005,Krish Malhotra,C5
BT202502006,Ira Narayan,C2
BT202502006,Ira Narayan,C9
BT202502006,Ira Narayan,C13
BT202502007,Dev Goyal,C5
BT202502007,Dev Goyal,C7
BT202502007,Dev Goyal,C12
BT202502008,Shruti Menon,C6
BT202502008,Shruti Menon,C10
BT202502008,Shruti Menon,C16
IMT202501001,Aishwarya Menon,C6
IMT202501001,Aishwarya Menon,C15
IMT202501001,Aishwarya Menon,C12
IMT202501002,Neel Kolhe,C7
IMT202501002,Neel Kolhe,C8
IMT202501002,Neel Kolhe,C5
IMT202501003,Vishal Singh,C1
IMT202501003,Vishal Singh,C9
IMT202501003,Vishal Singh,C11
IMT202501004,Ritika Shah,C2
IMT202501004,Ritika Shah,C10
IMT202501004,Ritika Shah,C14
IMT202501005,Akash Das,C3
IMT202501005,Akash Das,C11
IMT202501005,Akash Das,C16"""

@st.cache_data
def load_data():
    """Loads and preprocesses all necessary data."""
    try:
        df_courses = pd.read_csv('courses.csv')
    except FileNotFoundError:
        st.error("Error: 'courses.csv' not found. Ensure it's in the same directory.")
        st.stop()
        
    df_students = pd.read_csv(StringIO(STUDENTS_CSV_CONTENT))
    
    try:
        with open('timetable_output.json', 'r') as f:
            schedule_data = json.load(f)
        df_schedule = pd.DataFrame(schedule_data)
    except FileNotFoundError:
        st.error("Error: 'timetable_output.json' not found. Please run generate_timetable.py first.")
        st.stop()
    except Exception as e:
        st.error(f"Error loading schedule data: {e}")
        st.stop()
        
    return df_courses, df_students, df_schedule

# ==========================================
# 2. APP LOGIC
# ==========================================

def get_student_schedule(student_id, df_students, df_schedule, df_courses):
    """Filters the master schedule for a specific student ID."""
    
    # 1. Get the list of Course IDs (CIDs) the student is enrolled in
    enrolled_cids = df_students[df_students['student_id'] == student_id]['course_id'].tolist()
    
    if not enrolled_cids:
        return None, None
    
    # Get student name
    student_name = df_students[df_students['student_id'] == student_id]['student_name'].iloc[0]

    # 2. Filter the master schedule by the enrolled CIDs
    student_sched = df_schedule[df_schedule['Course'].isin(enrolled_cids)].copy()
    
    # 3. Format for display (Pivot Table)
    day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    
    if student_sched.empty:
        return student_name, pd.DataFrame()

    # Create a nice display entry with Title (Room)
    student_sched['Display_Entry'] = student_sched.apply(
        lambda row: f"{row['Title'].split('-')[0]} ({row['Room']})", axis=1
    )
    
    # Pivot the data to create the weekly grid
    pivot_table = student_sched.pivot_table(
        index='Slot', 
        columns='Day', 
        values='Display_Entry', 
        aggfunc=lambda x: '<br>'.join(x) # Use <br> for multiple classes in one slot (should be rare/non-existent)
    ).fillna('')
    
    # Reorder the columns
    existing_days = [d for d in day_order if d in pivot_table.columns]
    pivot_table = pivot_table.reindex(columns=existing_days)
    
    # Add CSS for better readability in Streamlit
    def format_timetable(df):
        return df.style.set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#f0f2f6'), ('color', '#1f77b4')]},
            {'selector': 'td', 'props': [('text-align', 'center'), ('vertical-align', 'middle'), ('height', '50px')]}
        ]).to_html()

    return student_name, pivot_table

# ==========================================
# 3. STREAMLIT UI
# ==========================================

def main():
    st.set_page_config(layout="wide")
    st.title("📅 OptiTime: Student Timetable Viewer")
    st.markdown("Use this interface to view the generated weekly schedule for any student.")

    df_courses, df_students, df_schedule = load_data()
    
    # Get all unique student IDs for the dropdown
    student_ids = sorted(df_students['student_id'].unique().tolist())
    
    # Sidebar for selection
    st.sidebar.header("Select Student")
    selected_id = st.sidebar.selectbox(
        "Student ID",
        student_ids
    )

    if selected_id:
        student_name, student_timetable = get_student_schedule(selected_id, df_students, df_schedule, df_courses)
        
        if student_timetable is None:
            st.warning(f"Student ID: {selected_id} not found in the student records.")
            return

        st.header(f"Schedule for: {student_name} ({selected_id})")
        
        if student_timetable.empty:
            st.info("This student is not scheduled for any courses this week based on the current timetable.")
        else:
            # Display the timetable as an HTML table for styling
            st.markdown(student_timetable.to_html(escape=False), unsafe_allow_html=True)
            
            st.subheader("Enrolled Courses")
            
            # Show a list of all courses this student is taking
            enrolled_cids = df_students[df_students['student_id'] == selected_id]['course_id'].tolist()
            enrolled_details = df_courses[df_courses['course_id'].isin(enrolled_cids)][['course_id', 'title', 'instructor1', 'credits']]
            enrolled_details.columns = ['ID', 'Title', 'Instructor', 'Credits']
            st.dataframe(enrolled_details, hide_index=True, use_container_width=True)

if __name__ == "__main__":
    main()
