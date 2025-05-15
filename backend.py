from flask import Flask, request, jsonify
from models import db, User
import joblib
from sentence_transformers import SentenceTransformer
from datetime import datetime
import requests
import math


OPENROUTER_API_KEY = "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"


app = Flask(__name__)

model = joblib.load("duration_model.pkl")
encoder = joblib.load("encoder.pkl")
bert = SentenceTransformer("all-MiniLM-L6-v2")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists."}), 400

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully."}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        return jsonify({"message": "Login successful."}), 200
    else:
        return jsonify({"error": "Invalid username or password."}), 401



@app.route('/generate_plan', methods=['POST'])
def generate_plan():
    data = request.json or {}
    summary = data.get("summary")

    if not summary:
        task_id = request.args.get("id")
        if not task_id:
            return jsonify({"error": "Please provide a summary or task ID."}), 400

        task = AssignedTask.query.get(task_id)
        if not task:
            return jsonify({"error": "Task not found."}), 404
        summary = task.summary

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://yourproject.local", # it doesnt matter what did you write
        "X-Title": "SmartTaskPlanner"
    }

    
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that generates structured, numbered sub-tasks for software development tasks. Return only the list."
            },
            {
                "role": "user",
                "content": f"Break down the following task into detailed, numbered steps:\n\n{summary}"
            }
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
        if response.status_code != 200:
            return jsonify({"error": f"API error: {response.status_code}"}), response.status_code

        plan_text = response.json()['choices'][0]['message']['content']

        if task_id and task:
            task.task_plan = plan_text
            db.session.commit()

        return jsonify({"plan": plan_text}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    


from flask import request, jsonify
from models import AssignedTask

@app.route('/assign_task', methods=['POST'])  # Assign a task
def assign_task():
    data = request.json

    assigned_to = data['assigned_to']
    task_name = data['task_name']
    summary = data['summary']
    category = data['category']
    subcategory = data['subcategory']
    priority = data['priority']

    expected_duration = data.get('expected_duration')

    if expected_duration is None:
        from sentence_transformers import SentenceTransformer
        import joblib
        import numpy as np

        bert = SentenceTransformer("all-MiniLM-L6-v2")
        model = joblib.load("duration_model.pkl")
        encoder = joblib.load("encoder.pkl")

        embed = bert.encode([summary])
        encoded_cat = encoder.transform([[category, subcategory]])
        priority_val = np.array([[priority]])
        X_input = np.hstack([embed, encoded_cat, priority_val])

        log_pred = model.predict(X_input)[0]
        expected_duration = round(np.expm1(log_pred), 2)
        raw_duration = np.expm1(log_pred)
        hours = int(raw_duration)
        minutes = int((raw_duration - hours) * 60)
        expected_duration = float(f"{hours}.{minutes:02d}")


        print(f"🔮 AI Estimated Duration: {expected_duration} hours")

    new_task = AssignedTask(
        assigned_to=assigned_to,
        task_name=task_name,
        summary=summary,
        priority=priority,
        category=category,
        subcategory=subcategory,
        expected_duration=expected_duration
    )

    db.session.add(new_task)
    db.session.commit()

    return jsonify({
        "message": f"Task assigned to {assigned_to}.",
        "task_id": new_task.id,
        "estimated_duration": expected_duration
    }), 201


@app.route('/my_tasks', methods=['GET'])  # User task list
def get_my_tasks():
    username = request.args.get('user')
    if not username:
        return jsonify({"error": "Username not specified!"}), 400

    tasks = AssignedTask.query.filter_by(assigned_to=username).all()
    task_list = []
    for task in tasks:
        task_list.append({
            'id': task.id,
            'task_name': task.task_name,
            'summary': task.summary,
            'priority': task.priority,
            'category': task.category,
            'subcategory': task.subcategory,
            'expected_duration': task.expected_duration,
            'status': task.status,
            'start_time': task.start_time,
            'end_time': task.end_time,
            'actual_duration': task.actual_duration,
            'delay_reason': task.delay_reason,
            'performance_status': task.performance_status,
             "task_plan": task.task_plan
        })

    return jsonify(task_list), 200


@app.route('/start_task', methods=['POST'])  # Start task by ID
def start_task():
    task_id = request.args.get('id')
    if not task_id:
        return jsonify({"error": "Task ID not specified!"}), 400

    task = AssignedTask.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found."}), 404

    if task.status != "not_started":
        return jsonify({"message": "This task has already been started or completed."}), 400

    task.start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    task.status = "in_progress"
    db.session.commit()

    return jsonify({
        "message": f"Task ID {task_id} started.",
        "start_time": task.start_time
    }), 200


@app.route('/complete_task', methods=['POST'])  # Complete task by ID
def complete_task():
    task_id = request.args.get('id')
    if not task_id:
        return jsonify({"error": "Task ID not specified!"}), 400

    task = AssignedTask.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found."}), 404

    if task.status != "in_progress":
        return jsonify({"message": "This task has not been started or is already completed."}), 400

    # Save end time
    task.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Calculate duration
    start = datetime.strptime(task.start_time, '%Y-%m-%d %H:%M:%S')
    end = datetime.strptime(task.end_time, '%Y-%m-%d %H:%M:%S')
    duration = (end - start).total_seconds() / 3600  # minutes

    task.actual_duration = round(duration, 2)
    task.status = "completed"

    # Evaluate performance
    ratio = duration / task.expected_duration
    if ratio <= 0.9:
        task.performance_status = "Excellent"
    elif ratio <= 1.0:
        task.performance_status = "Good"
    elif ratio <= 1.25:
        task.performance_status = "Average"
    elif ratio <= 1.5:
        task.performance_status = "Poor"
    else:
        task.performance_status = "Very Poor"

    # Require delay_reason if late
    if ratio > 1.0:
        data = request.json or {}
        delay_reason = data.get("delay_reason")
        if not delay_reason:
            return jsonify({"error": "Delay reason required for overdue tasks."}), 400
        task.delay_reason = delay_reason

    db.session.commit()

    return jsonify({
        "message": f"Task ID {task_id} completed.",
        "actual_duration": task.actual_duration,
        "performance_status": task.performance_status
    }), 200



@app.route('/manager_dashboard', methods=['GET'])  # Manager overview
def manager_dashboard():
    tasks = AssignedTask.query.all()
    dashboard = []

    for task in tasks:
        dashboard.append({
            "id": task.id,
            "assigned_to": task.assigned_to,
            "task_name": task.task_name,
            "summary": task.summary,
            "priority": task.priority,
            "category": task.category,
            "subcategory": task.subcategory,
            "expected_duration": task.expected_duration,
            "actual_duration": task.actual_duration,
            "status": task.status,
            "performance_status": task.performance_status,
            "delay_reason": task.delay_reason,
            "start_time": task.start_time,
            "end_time": task.end_time,
            "task_steps": task.task_steps,
            "color": get_color_for_status(task.performance_status)
        })

    return jsonify(dashboard), 200


@app.route('/user_stats', methods=['GET'])  # User performance stats
def user_stats():
    tasks = AssignedTask.query.all()
    stats = {}

    for task in tasks:
        user = task.assigned_to
        if user not in stats:
            stats[user] = {
                "total_tasks": 0,
                "Excellent": 0,
                "Good": 0,
                "Average": 0,
                "Poor": 0,
                "Very Poor": 0
            }
        stats[user]["total_tasks"] += 1
        if task.performance_status:
            stats[user][task.performance_status] += 1

    return jsonify(stats), 200


import csv
from io import StringIO
from flask import Response

@app.route('/export_tasks', methods=['GET'])  # Export all assigned tasks
def export_tasks():
    tasks = AssignedTask.query.all()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "id", "assigned_to", "task_name", "summary", "category", "subcategory", "priority",
        "expected_duration", "actual_duration", "status", "start_time", "end_time",
        "performance_status", "delay_reason"
    ])

    for t in tasks:
        writer.writerow([
            t.id,
            t.assigned_to,
            t.task_name,
            t.summary,
            t.category,
            t.subcategory,
            t.priority,
            t.expected_duration,
            t.actual_duration,
            t.status,
            t.start_time,
            t.end_time,
            t.performance_status,
            t.delay_reason
        ])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=tasks.csv"}
    )



@app.route('/tasks_by_date', methods=['GET'])  # Filter tasks by end date
def tasks_by_date():
    days = int(request.args.get("days", 1))
    now = datetime.now()
    tasks = AssignedTask.query.all()

    filtered = []
    for task in tasks:
        if task.end_time:
            end = datetime.strptime(task.end_time, '%Y-%m-%d %H:%M:%S')
            if (now - end).days <= days:
                filtered.append({
                    "task_name": task.task_name,
                    "user": task.assigned_to,
                    "end_time": task.end_time,
                    "performance_status": task.performance_status
                })

    return jsonify(filtered), 200


def get_color_for_status(status):
    if status == "Excellent":
        return "green"
    elif status == "Good":
        return "lightgreen"
    elif status == "Average":
        return "orange"
    elif status == "Poor":
        return "red"
    elif status == "Very Poor":
        return "darkred"
    return "gray"



@app.route('/delete_tasks_by_id', methods=['DELETE'])  # Delete task by ID
def delete_task_by_id():
    task_id = request.args.get('id')
    if not task_id:
        return jsonify({"error": "ID not specified!"}), 400

    task = AssignedTask.query.get(task_id)  
    if not task:
        return jsonify({"error": "No task found with specified ID."}), 404

    username = task.assigned_to  
    db.session.delete(task)
    db.session.commit()

    return jsonify({
        "message": f"Task with ID {task_id} assigned to {username} was deleted!"
    }), 200


@app.route('/hourly_performance', methods=['GET'])
def hourly_performance():
    tasks = AssignedTask.query.filter(AssignedTask.status == "completed").all()
    hourly_stats = {f"{i:02d}": 0 for i in range(24)}

    for task in tasks:
        if task.start_time and task.performance_status:
            start_hour = datetime.strptime(task.start_time, '%Y-%m-%d %H:%M:%S').hour
            if task.performance_status == "Excellent":
                hourly_stats[f"{start_hour:02d}"] += 1

    return jsonify(hourly_stats), 200


from collections import defaultdict


@app.route('/hourly_efficiency', methods=['GET'])
def hourly_efficiency():
    tasks = AssignedTask.query.filter_by(status="completed").all()
    hourly_data = defaultdict(lambda: defaultdict(list))  # user -> hour -> efficiencies

    for task in tasks:
        if task.start_time and task.actual_duration:
            try:
                start_hour = datetime.strptime(task.start_time, '%Y-%m-%d %H:%M:%S').hour
                efficiency = task.expected_duration / task.actual_duration if task.actual_duration else 0
                hourly_data[task.assigned_to][start_hour].append(efficiency)
            except:
                continue

    result = []
    for user, hours in hourly_data.items():
        for hour, values in hours.items():
            avg_eff = round(sum(values) / len(values), 2)
            result.append({"user": user, "hour": hour, "efficiency": avg_eff})

    return jsonify(result), 200

@app.route('/update_steps', methods=['POST'])
def update_steps():
    data = request.json
    task_id = data.get("task_id")
    steps = data.get("steps")

    task = AssignedTask.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    task.task_steps = steps
    db.session.commit()
    return jsonify({"message": "Steps updated"}), 200



if __name__ == '__main__':
    with app.app_context():
        #db.drop_all()
        db.create_all()
    app.run(debug=True)
