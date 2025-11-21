import streamlit as st
import pandas as pd
import json
import plotly.express as px

# ==========================================
# CONFIG & STYLING
# ==========================================
st.set_page_config(
    page_title="OptiTime Dashboard",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stDataFrame {font-size: 14px;}
    div[data-testid="stMetricValue"] {font-size: 24px;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATA SETUP
# ==========================================

@st.cache_data
def load_data():
    """Loads and preprocesses all necessary data."""
    
    # 1. Load Courses
    try:
        df_courses = pd.read_csv('courses.csv')
    except FileNotFoundError:
        st.error("❌ Error: 'courses.csv' not found. Ensure it's in the same directory.")
        st.stop()
        
    # 2. Load Students (Now reading from external file)
    try:
        df_students = pd.read_csv('enrollments.csv')
        # Optional: specific check to ensure columns exist
        required_cols = ['student_id', 'student_name', 'course_id']
        if not all(col in df_students.columns for col in required_cols):
            st.error(f"❌ Error: 'enrollments.csv' must contain columns: {required_cols}")
            st.stop()
    except FileNotFoundError:
        st.error("❌ Error: 'enrollments.csv' not found. Please create this file.")
        st.stop()
    
    # 3. Load Schedule
    try:
        with open('timetable_output.json', 'r') as f:
            schedule_data = json.load(f)
        df_schedule = pd.DataFrame(schedule_data)
    except FileNotFoundError:
        st.error("❌ Error: 'timetable_output.json' not found. Please run generate_timetable.py first.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error loading schedule data: {e}")
        st.stop()
        
    return df_courses, df_students, df_schedule

# ==========================================
# 3. LOGIC FUNCTIONS
# ==========================================

def style_timetable(val):
    """Helper function to colorize non-empty cells."""
    if isinstance(val, str) and len(val) > 1:
        # A nice soft blue for classes
        return 'background-color: #dbeafe; color: #1e3a8a; font-weight: bold; border-radius: 4px;'
    return 'background-color: #ffffff; color: #e5e7eb;' # Faded text for empty

def get_student_data(student_id, df_students, df_schedule, df_courses):
    """Filters data for a specific student."""
    
    # Get Basic Info
    student_info = df_students[df_students['student_id'] == student_id]
    if student_info.empty:
        return None, None, None, None
        
    student_name = student_info['student_name'].iloc[0]
    enrolled_cids = student_info['course_id'].tolist()
    
    # Get Schedule
    student_sched = df_schedule[df_schedule['Course'].isin(enrolled_cids)].copy()
    
    # Get Course Details
    course_details = df_courses[df_courses['course_id'].isin(enrolled_cids)].copy()
    
    return student_name, student_sched, course_details, enrolled_cids

def create_timetable_grid(df_sched):
    """Transforms linear schedule data into a grid."""
    if df_sched.empty:
        return pd.DataFrame()

    day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    
    # Cleaner display string
    df_sched['Display'] = df_sched.apply(
        lambda row: f"{row['Course']} ({row['Room']})", axis=1
    )
    
    # Pivot
    pivot = df_sched.pivot_table(
        index='Slot', 
        columns='Day', 
        values='Display', 
        aggfunc=lambda x: ', '.join(x)
    ).fillna('')
    
    # Reorder Columns
    existing_days = [d for d in day_order if d in pivot.columns]
    pivot = pivot.reindex(columns=existing_days)
    
    # Sort Rows (Slots) - Assuming Slot strings sort alphabetically okay, otherwise mapped sort needed
    pivot = pivot.sort_index()
    
    return pivot

# ==========================================
# 4. MAIN UI
# ==========================================

def main():
    df_courses, df_students, df_schedule = load_data()

    # --- SIDEBAR ---
    st.sidebar.title("🎓 OptiTime Navigator")
    
    # Student Selector
    student_ids = sorted(df_students['student_id'].unique().tolist())
    
    # Optional: format selector to show name + ID
    format_func = lambda x: f"{x} - {df_students[df_students['student_id']==x]['student_name'].iloc[0]}"
    
    selected_id = st.sidebar.selectbox(
        "Select Student",
        student_ids,
        format_func=format_func
    )
    
    # --- DATA PROCESSING ---
    name, s_sched, s_courses, enrolled_cids = get_student_data(selected_id, df_students, df_schedule, df_courses)

    if not name:
        st.error("Student not found.")
        return

    # --- HEADER ---
    st.title(f"Welcome, {name}")
    st.markdown(f"**Student ID:** `{selected_id}`")
    st.markdown("---")

    # --- TOP METRICS ---
    # Calculate stats
    total_credits = s_courses['credits'].sum() if 'credits' in s_courses.columns else 0
    total_classes = len(s_sched)
    
    if not s_sched.empty:
        busiest_day = s_sched['Day'].mode()[0]
    else:
        busiest_day = "N/A"

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Credits", total_credits, delta_color="off")
    col2.metric("Weekly Classes", total_classes, "Sessions")
    col3.metric("Busiest Day", busiest_day)
    
    st.markdown("---")

    # --- TABS ---
    tab1, tab2, tab3 = st.tabs(["📅 Weekly Timetable", "📚 Course Details", "📊 Analytics"])

    # --- TAB 1: TIMETABLE ---
    with tab1:
        if s_sched.empty:
            st.info("No classes scheduled for this week.")
        else:
            grid = create_timetable_grid(s_sched)
            
            st.subheader("Weekly View")
            
            # Use Pandas Styler for a much cleaner look
            st.dataframe(
                grid.style.map(style_timetable),
                use_container_width=True,
                height=(len(grid) + 1) * 35 + 3  # Dynamic height adjustment
            )
            
            # Download Button
            csv = grid.to_csv().encode('utf-8')
            st.download_button(
                label="📥 Download Schedule (CSV)",
                data=csv,
                file_name=f"{selected_id}_timetable.csv",
                mime='text/csv',
            )

    # --- TAB 2: COURSE DETAILS ---
    with tab2:
        st.subheader("Enrolled Courses")
        if s_courses.empty:
            st.warning("No enrollment records found.")
        else:
            # Clean up columns for display
            display_courses = s_courses[['course_id', 'title', 'instructor1', 'credits']].rename(
                columns={'course_id': 'ID', 'title': 'Course Title', 'instructor1': 'Instructor', 'credits': 'Credits'}
            )
            st.dataframe(
                display_courses, 
                hide_index=True, 
                use_container_width=True,
                column_config={
                    "Credits": st.column_config.NumberColumn(format="%d pts")
                }
            )

    # --- TAB 3: ANALYTICS ---
    with tab3:
        st.subheader("Workload Distribution")
        
        if s_sched.empty:
            st.info("No data to visualize.")
        else:
            # Prepare data for plotting
            daily_counts = s_sched['Day'].value_counts().reset_index()
            daily_counts.columns = ['Day', 'Classes']
            
            # Enforce order of days
            day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
            daily_counts['Day'] = pd.Categorical(daily_counts['Day'], categories=day_order, ordered=True)
            daily_counts = daily_counts.sort_values('Day')

            # Plotly Bar Chart
            fig = px.bar(
                daily_counts, 
                x='Day', 
                y='Classes', 
                color='Classes',
                color_continuous_scale='Blues',
                title="Number of Classes per Day",
                text_auto=True
            )
            fig.update_layout(xaxis_title="", yaxis_title="Class Count", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
