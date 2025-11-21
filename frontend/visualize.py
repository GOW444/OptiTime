import streamlit as st
import pandas as pd
import json
import plotly.express as px
import datetime

# ==========================================
# CONFIG & STYLING
# ==========================================
st.set_page_config(
    page_title="OptiTime Dashboard",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
<style>
   .stDataFrame {font-size: 14px;}
   div[data-testid="stMetricValue"] {font-size: 24px;}
</style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# DATA SETUP
# ==========================================
@st.cache_data
def load_data():
    df_courses = pd.DataFrame()
    df_students = pd.DataFrame()
    df_schedule = pd.DataFrame()

    try:
        df_courses = pd.read_csv("courses.csv")
    except Exception as e:
        st.error(f"❌ Error reading 'courses.csv': {e}")
        return df_courses, df_students, df_schedule

    try:
        df_students = pd.read_csv("enrollments.csv")
        required_cols = ["student_id", "student_name", "course_id"]
        if not all(col in df_students.columns for col in required_cols):
            st.error(f"❌ 'enrollments.csv' missing required columns.")
            return df_courses, pd.DataFrame(), df_schedule
    except Exception as e:
        st.error(f"❌ Error reading 'enrollments.csv': {e}")
        return df_courses, pd.DataFrame(), df_schedule

    try:
        with open("new_timetable_output.json", "r") as f:
            schedule_data = json.load(f)
        df_schedule = pd.DataFrame(schedule_data)
    except Exception as e:
        st.error(f"❌ Error loading schedule JSON: {e}")
        return df_courses, df_students, pd.DataFrame()

    return df_courses, df_students, df_schedule


# ==========================================
# LOGIC
# ==========================================
def style_timetable(val):
    try:
        if isinstance(val, str) and len(val.strip()) > 0:
            return "background-color: #dbeafe; color: #1e3a8a; font-weight: bold; border-radius: 4px;"
        return "background-color: #ffffff; color: #6b7280;"
    except Exception:
        return ""


def get_student_data(student_id, df_students, df_schedule, df_courses):
    if df_students.empty:
        return None, pd.DataFrame(), pd.DataFrame(), []

    student_info = df_students[df_students["student_id"] == student_id]
    if student_info.empty:
        return None, pd.DataFrame(), pd.DataFrame(), []

    student_name = student_info["student_name"].iloc[0]
    enrolled_cids = student_info["course_id"].tolist()

    if not df_schedule.empty and "Course" in df_schedule.columns:
        student_sched = df_schedule[df_schedule["Course"].isin(enrolled_cids)]
    else:
        student_sched = pd.DataFrame()

    if not df_courses.empty and "course_id" in df_courses.columns:
        s_courses = df_courses[df_courses["course_id"].isin(enrolled_cids)]
    else:
        s_courses = pd.DataFrame()

    return student_name, student_sched, s_courses, enrolled_cids


def create_timetable_grid(df_sched):
    if df_sched is None or df_sched.empty:
        return pd.DataFrame()

    if "Slot" not in df_sched.columns or "Day" not in df_sched.columns:
        return pd.DataFrame()

    if "Course" not in df_sched.columns:
        df_sched["Course"] = ""
    if "Room" not in df_sched.columns:
        df_sched["Room"] = ""

    df_sched["Display"] = df_sched.apply(
        lambda r: f"{r['Course']} ({r['Room']})" if str(r["Course"]).strip() else "",
        axis=1,
    )

    pivot = (
        df_sched.pivot_table(
            index="Slot",
            columns="Day",
            values="Display",
            aggfunc=lambda x: ", ".join([str(i) for i in x if str(i).strip()]),
        )
        .fillna("")
    )

    day_order = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    existing = [d for d in day_order if d in pivot.columns]
    pivot = pivot[existing]

    return pivot.sort_index()


# ==========================================
# MAIN UI
# ==========================================
def main():
    df_courses, df_students, df_schedule = load_data()

    st.sidebar.title("🎓 OptiTime Navigator")

    if df_students.empty:
        st.warning("No student/enrollment data found.")
        return

    student_ids = sorted(df_students["student_id"].unique())
    if not student_ids:
        st.warning("No students found.")
        return

    def format_func(x):
        row = df_students[df_students["student_id"] == x]
        if not row.empty:
            return f"{x} - {row['student_name'].iloc[0]}"
        return str(x)

    selected_id = st.sidebar.selectbox("Select Student", student_ids, format_func=format_func)

    name, s_sched, s_courses, enrolled_cids = get_student_data(
        selected_id, df_students, df_schedule, df_courses
    )
        # Header
    st.title(f"Welcome, {name}")
    st.markdown(f"**Student ID:** `{selected_id}`")
    st.markdown("---")


    # === Today's Schedule ===
    day_map = {
        0: "Mon",
        1: "Tue",
        2: "Wed",
        3: "Thu",
        4: "Fri",
        5: "Sat",
        6: "Sun",
    }
    today_label = day_map[datetime.datetime.today().weekday()]

    today_sched = s_sched[s_sched["Day"] == today_label] if not s_sched.empty else pd.DataFrame()

    st.subheader(f"Today's Schedule ({today_label})")

    if today_sched.empty:
        st.info("No classes today.")
    else:
        today_grid = create_timetable_grid(today_sched)
        st.dataframe(today_grid.style.map(style_timetable), use_container_width=True)

    if not name:
        st.error("Student not found.")
        return

    # Metrics
    total_credits = (
        s_courses["credits"].sum() if (not s_courses.empty and "credits" in s_courses.columns) else 0
    )
    total_classes = len(s_sched) if not s_sched.empty else 0
    busiest_day = s_sched["Day"].mode()[0] if not s_sched.empty else "N/A"

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Credits", int(total_credits))
    c2.metric("Weekly Classes", total_classes, "Sessions")
    c3.metric("Busiest Day", busiest_day)

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📅 Weekly Timetable", "📚 Course Details", "📊 Analytics"])

    # Tab 1
    with tab1:
        if s_sched.empty:
            st.info("No classes scheduled.")
        else:
            grid = create_timetable_grid(s_sched)
            if grid.empty:
                st.info("Schedule present but missing Slot/Day columns.")
            else:
                st.dataframe(
                    grid.style.applymap(style_timetable),
                    use_container_width=True,
                    height=(len(grid) + 1) * 35 + 3,
                )
                st.download_button(
                    "📥 Download Schedule (CSV)",
                    grid.to_csv().encode("utf-8"),
                    file_name=f"{selected_id}_timetable.csv",
                    mime="text/csv",
                )

    # Tab 2
    with tab2:
        if s_courses.empty:
            st.warning("No enrollment records.")
        else:
            cols = [c for c in ["course_id", "title", "instructor1", "credits"] if c in s_courses.columns]
            display_courses = s_courses[cols].rename(
                columns={
                    "course_id": "ID",
                    "title": "Course Title",
                    "instructor1": "Instructor",
                    "credits": "Credits",
                }
            )
            st.dataframe(display_courses, hide_index=True, use_container_width=True)

    # Tab 3
    with tab3:
        if s_sched.empty or "Day" not in s_sched.columns:
            st.info("No data to visualize.")
        else:
            daily_counts = s_sched["Day"].value_counts().reset_index()
            daily_counts.columns = ["Day", "Classes"]
            day_order = ["Mon", "Tue", "Wed", "Thu", "Fri"]
            daily_counts["Day"] = pd.Categorical(daily_counts["Day"], categories=day_order, ordered=True)
            daily_counts = daily_counts.sort_values("Day")

            fig = px.bar(
                daily_counts,
                x="Day",
                y="Classes",
                color="Classes",
                color_continuous_scale="Blues",
                title="Number of Classes per Day",
                text_auto=True,
            )
            fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Class Count")
            st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()

