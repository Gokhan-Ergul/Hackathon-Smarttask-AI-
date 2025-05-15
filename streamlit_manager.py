import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Manager Panel", layout="wide")

# Stil: Açık tema + selectbox cursor ayarı
st.markdown("""
    <style>
    .stSelectbox > div > div:first-child {
        cursor: pointer !important;
    }
    body {
        background-color: #F7F7F7;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='color: #FBC02D;'>🧠 Manager Panel</h1>", unsafe_allow_html=True)
BASE_URL = "http://127.0.0.1:5000"
st.markdown("<hr>", unsafe_allow_html=True)

# 🔲 Kart kutusu
def section_container(title, content_block):
    with st.container():
        st.markdown(
            f"<div style='background-color:#F2F2F2; color:#2C2C2C; padding:20px; "
            f"border-radius:12px; margin-bottom:25px; border:1px solid #DDD;'>"
            f"<h4 style='color:#4A90E2;'>{title}</h4>",
            unsafe_allow_html=True
        )
        content_block()
        st.markdown("</div>", unsafe_allow_html=True)

# 📌 Assign New Task
def assign_task_section():
    with st.form("assign_form"):
        col1, col2 = st.columns(2)
        with col1:
            assigned_to = st.text_input("👤 Username")
            task_name = st.text_input("📝 Task Name")
            summary = st.text_area("📋 Summary")
        with col2:
            priority = st.selectbox("📊 Priority", list(range(1, 11)))
            category = st.text_input("🗂️ Category")
            subcategory = st.text_input("📁 Subcategory")
            expected_duration = st.text_input("⏳ Expected Duration (hours) (optional)", help="Leave blank to let AI estimate it")

        if st.form_submit_button("✅ Assign Task"):
            payload = {
                "assigned_to": assigned_to,
                "task_name": task_name,
                "summary": summary,
                "priority": priority,
                "category": category,
                "subcategory": subcategory
            }
            if expected_duration.strip():
                try:
                    payload["expected_duration"] = float(expected_duration)
                except ValueError:
                    st.warning("⚠️ Duration must be a number.")
                    return

            res = requests.post(f"{BASE_URL}/assign_task", json=payload)
            if res.status_code == 201:
                st.success(res.json().get("message"))
            else:
                try:
                    st.error(res.json().get("error", "Unknown error"))
                except Exception:
                    st.error(f"❌ Unexpected response: {res.text}")

section_container("📌 Assign New Task", assign_task_section)

# 📊 All Tasks Dashboard
def dashboard_section():
    if st.button("📥 Load All Tasks"):
        res = requests.get(f"{BASE_URL}/manager_dashboard")
        if res.status_code == 200:
            
            tasks = res.json()
            

            for task in tasks:
                steps = task.get("task_steps")
                if steps:
                    total = len(steps)
                    done = sum(1 for v in steps.values() if v)
                    percent = int(100 * done / total) if total else 0
                    task["subtask_progress"] = f"{percent}%"
                else:
                    task["subtask_progress"] = "-"
            
            #df = pd.DataFrame(tasks)

            columns_order = [
                "id", "assigned_to", "task_name", "category", "subcategory", "priority",
                "expected_duration", "actual_duration", "status", "start_time", "end_time",
                "performance_status", "delay_reason","subtask_progress"
            ]
            
            df = pd.DataFrame(tasks)[columns_order]

            df.columns = [
                "ID", "Assigned To", "Task Name", "Category", "Subcategory", "Priority",
                "Expected Duration (h)", "Actual Duration (h)", "Status", "Start Time",
                "End Time", "Performance", "Delay Reason","Subtask Progress"
            ]
            st.dataframe(df, use_container_width=True)

section_container("📊 All Tasks Dashboard", dashboard_section)

# 📈 Performance Stats
def stats_section():
    show_stats = st.checkbox("📈 Show User Stats")
    if show_stats:
        res = requests.get(f"{BASE_URL}/user_stats")
        if res.status_code == 200:
            stats = res.json()
            for user, data in stats.items():
                with st.container():
                    st.markdown(f"""
                        <div style='background-color:#F7F7F7; padding:15px; border-radius:10px; margin-bottom:15px; border: 1px solid #DDD;'>
                            <h4 style='color:#4A90E2;'>👤 {user}</h4>
                            <p>
                                <span style='background-color:#81C784; padding:4px 8px; border-radius:5px;'>Excellent: {data.get('Excellent', 0)}</span>
                                <span style='background-color:#AED581; padding:4px 8px; border-radius:5px;'>Good: {data.get('Good', 0)}</span>
                                <span style='background-color:#FFD54F; padding:4px 8px; border-radius:5px;'>Average: {data.get('Average', 0)}</span>
                                <span style='background-color:#FF8A65; padding:4px 8px; border-radius:5px;'>Poor: {data.get('Poor', 0)}</span>
                                <span style='background-color:#E57373; padding:4px 8px; border-radius:5px;'>Very Poor: {data.get('Very Poor', 0)}</span>
                            </p>
                            <p><strong>Total Tasks:</strong> {data.get('total_tasks', 0)}</p>
                        </div>
                    """, unsafe_allow_html=True)


section_container("📈 Performance Stats", stats_section)

# 📤 Export Tasks
def export_csv_section():
    if st.button("📁 Export CSV"):
        res = requests.get(f"{BASE_URL}/export_tasks")
        if res.status_code == 200:
            st.download_button(
                label="⬇️ Download CSV",
                data=res.content,
                file_name='tasks.csv',
                mime='text/csv'
            )
        else:
            st.error("❌ Failed to export CSV.")

section_container("📤 Export Tasks as CSV", export_csv_section)

# 🗓️ Tasks Completed in X Days
def date_filter_section():
    days = st.slider("Select number of days", min_value=1, max_value=30, value=7)
    if st.button("🔍 Filter by Date"):
        res = requests.get(f"{BASE_URL}/tasks_by_date", params={"days": days})
        if res.status_code == 200:
            data = res.json()
            df = pd.DataFrame(data)
            if not df.empty:
                df['end_time'] = pd.to_datetime(df['end_time'])
                df['duration_days'] = (pd.Timestamp.now() - df['end_time']).dt.days
                for _, row in df.iterrows():
                    color = '#66BB6A' if row['duration_days'] <= 10 else '#FFCA28' if row['duration_days'] <= 20 else '#EF5350'
                    st.markdown(f"""
                        <div style='background-color:#F2F2F2; padding:12px; border-radius:10px; margin-bottom:10px; border: 1px solid #DDD;'>
                            <strong style='color:{color};'>Task:</strong> {row['task_name']}<br>
                            <strong style='color:{color};'>User:</strong> {row['user']}<br>
                            <strong style='color:{color};'>End Time:</strong> {row['end_time'].strftime('%Y-%m-%d %H:%M:%S')}<br>
                            <strong style='color:{color};'>Performance:</strong> {row['performance_status']}<br>
                            <div style='height:10px; background-color:{color}; border-radius:5px; margin-top:5px;'></div>
                        </div>
                    """, unsafe_allow_html=True)

section_container("🗓️ Tasks Completed in X Days", date_filter_section)

# ❌ Delete Task by ID
def delete_task_section():
    task_id = st.text_input("Enter Task ID to delete")
    if st.button("🗑️ Delete Task"):
        res = requests.delete(f"{BASE_URL}/delete_tasks_by_id", params={"id": task_id})
        if res.status_code == 200:
            st.success(res.json().get("message"))
        else:
            try:
                st.error(res.json().get("error"))
            except Exception:
                st.error(f"❌ Unexpected response: {res.text}")

section_container("❌ Delete Task by ID", delete_task_section)

st.markdown("<h2 style='color:#FBC02D;'>📊 Hourly Performance Analysis</h2>", unsafe_allow_html=True)

if st.button("📥 Load Hourly Stats"):
    res = requests.get("http://127.0.0.1:5000/hourly_efficiency")
    if res.status_code == 200:
        data = pd.DataFrame(res.json())
        if not data.empty:
            pivot = data.pivot(index="user", columns="hour", values="efficiency").fillna(0)
            st.write("### 🔥 Efficiency by Hour (Expected / Actual)")
            fig, ax = plt.subplots(figsize=(12, 5))
            sns.heatmap(pivot, annot=True, cmap="YlGnBu", fmt=".2f", linewidths=0.5, ax=ax)
            st.pyplot(fig)
        else:
            st.info("No data available for completed tasks.")
    else:
        st.error("❌ Could not load hourly performance data.")
