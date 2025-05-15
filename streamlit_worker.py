import streamlit as st
import requests
import pandas as pd

BASE_URL = "http://127.0.0.1:5000"
st.set_page_config(page_title="Worker Panel", layout="wide")

if "username" not in st.session_state:
    st.markdown("<h1 style='color: #1E88E5;'>🔐 Worker Login</h1>", unsafe_allow_html=True)
    username_input = st.text_input("👤 Username")
    password_input = st.text_input("🔑 Password", type="password")

    if st.button("🔓 Login"):
        response = requests.post(f"{BASE_URL}/login", json={
            "username": username_input,
            "password": password_input
        })

        if response.status_code == 200:
            st.session_state["username"] = username_input
            st.success("✅ Login successful!")
            st.rerun()
        else:
            st.error("❌ Invalid credentials.")
    st.stop()

username = st.session_state["username"]
st.markdown(f"<h1 style='color: #FB8C00;'>👷 Welcome, {username}</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

res = requests.get(f"{BASE_URL}/my_tasks", params={"user": username})
if res.status_code == 200:
    tasks = res.json()
    if tasks:
        for task in tasks:
            with st.container():

                performance_color = {
                    "Excellent": "#4CAF50",
                    "Good": "#8BC34A",
                    "Average": "#FFC107",
                    "Poor": "#FF5722",
                    "Very Poor": "#D32F2F",
                }

                status_label = task["performance_status"] or "-"
                status_color = performance_color.get(task["performance_status"], "#FFFFFF")
                st.markdown(f"""
                    <div style='background-color:#F2F2F2; color:#111111; padding:20px;
                    border-radius:16px; margin-bottom:25px; box-shadow:0 2px 8px rgba(0,0,0,0.05);'>

                    <h4 style='margin-bottom:10px;'>📌 {task['task_name']} (ID: {task['id']})</h4>
                    <p><strong>📋 Summary:</strong> {task['summary']}</p>
                    <p><strong>🗂️ Category:</strong> {task['category']} / {task['subcategory']}</p>
                    <p><strong>📊 Priority:</strong> {task['priority']}</p>
                    <p><strong>⏳ Expected Duration:</strong> {task['expected_duration']} hours</p>
                    <p><strong>📍 Status:</strong> <span style='color:#FF7043'>{task['status']}</span></p>
                    <p><strong>🕓 Start:</strong> {task['start_time'] or '-'} | 
                       <strong>🕔 End:</strong> {task['end_time'] or '-'}</p>
                    <p><strong>⏱️ Duration:</strong> {task['actual_duration'] or '-'}</p>
                    <p><strong>📈 Performance:</strong> <span style='color:{status_color}'>{status_label}</span></p>
                    <p><strong>🔵 Delay Reason:</strong> {task['delay_reason'] or '-'}</p>
                """, unsafe_allow_html=True)

                
                if task["status"] == "not_started":
                    if st.button(f"▶️ Start Task #{task['id']}", key=f"start_{task['id']}"):
                        res = requests.post(f"{BASE_URL}/start_task", params={"id": task["id"]})
                        if res.status_code == 200:
                            st.success(res.json().get("message"))
                            st.rerun()
                        else:
                            st.error(res.json().get("message"))

                elif task["status"] == "in_progress":

                    with st.expander("💡 Need a step-by-step plan?"):
                        user_summary = st.text_area(
                            "✍️ Optionally enter a custom description for this task (leave empty to use manager's summary):",
                            key=f"custom_summary_{task['id']}"
                        )

                        if st.button(f"🧐 Get AI Action Plan for Task #{task['id']}", key=f"ai_plan_{task['id']}"):
                            payload = {}
                            if user_summary.strip():
                                payload["summary"] = user_summary.strip()

                            res_plan = requests.post(
                                f"{BASE_URL}/generate_plan",
                                params={"id": task["id"]},
                                json=payload,
                                headers={"Content-Type": "application/json"}
                            )

                            if res_plan.status_code == 200:
                                ai_plan = res_plan.json().get("plan", "No plan returned.")
                                st.markdown("### 🧐 AI Suggested Plan")
                                st.code(ai_plan, language="markdown")
                            else:
                                st.error(f"❌ Failed to generate AI plan: {res_plan.text}")

                    if task.get("task_plan"):
                        st.markdown("### ✅ Your AI Subtasks")
                        steps = [s.strip() for s in task["task_plan"].split('\n') if s.strip()]
                        existing_progress = task.get("task_steps", {})

                        updated_progress = {}
                        for i, step in enumerate(steps):
                            step_text = step.lstrip("0123456789. ").strip()
                            prev_value = existing_progress.get(str(i), False)
                            checked = st.checkbox(step_text, key=f"{task['id']}_step_{i}", value=prev_value)
                            updated_progress[str(i)] = checked

                        if steps:
                            progress = int(100 * sum(updated_progress.values()) / len(steps))
                            st.progress(progress)
                            st.caption(f"🧐 Completion: {progress}%")

                        if updated_progress != existing_progress:
                            if st.button(f"💾 Save Progress for Task #{task['id']}", key=f"save_{task['id']}"):
                                try:
                                    update_response = requests.post(f"{BASE_URL}/update_steps", json={
                                        "task_id": task["id"],
                                        "steps": updated_progress
                                    })
                                    st.success("✅ Progress saved!")
                                    st.write("📤 update_steps:", update_response.status_code, update_response.text)
                                except Exception as e:
                                    st.error(f"❌ Failed to save progress: {e}")


                    st.markdown("### ✅ Complete This Task")
                    reason = st.text_area("🕒 Delay Reason (only if late)", key=f"reason_{task['id']}")
                    if st.button(f"✔️ Complete Task #{task['id']}", key=f"complete_{task['id']}"):
                        payload = {"delay_reason": reason} if reason else {}
                        res = requests.post(
                            f"{BASE_URL}/complete_task",
                            params={"id": task["id"]},
                            json=payload
                        )
                        if res.status_code == 200:
                            result = res.json()
                            st.success(result.get("message"))
                            st.write(f"⏱️ Duration: {result.get('actual_duration')} hours")
                            st.write(f"📈 Performance: {result.get('performance_status')}")
                            st.rerun()
                        else:
                            st.error(res.json().get("error"))

                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("📟 No tasks found.")
else:
    st.error("❌ Could not load tasks.")
