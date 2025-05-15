# ⏱️ Hackathon-Smarttask-AI - AI-Powered Task & Time Management Platform



> 🥈 2nd place winner at Hackathon Aydın – Built in 30 hours!

**SmartTaskAI** is a time management and task assignment platform powered by AI. It provides managers and workers with real-time insights and tools to assign, track, and complete tasks efficiently.

## 🚀 Features

### 🧠 AI Capabilities

- 🔮 **Task Duration Estimation (Manager-side)**: Predicts how long a task will take based on its description using a fine-tuned NLP transformer regression model.
- ✅ **Subtask Generation (Worker-side)**: Breaks down complex tasks into checkbox-style actionable steps using an NLP model (GPT-powered).

### 👥 User Roles

- **Manager**:
  - 👤 Assign tasks to users (with manual or AI-predicted duration)
  - 🗂️ Provide task details including summary, category, subcategory, and priority
  - 📋 View all assigned tasks with full metadata and real-time status
  - 📈 Analyze user performance based on completion efficiency
  - 🕓 Visualize hourly performance (e.g., which hours users are most efficient)
  - 🗓️ Filter completed tasks by the number of days (e.g., last 7 days)
  - 📁 Export all tasks and data as a CSV file
  - 🗑️ Delete tasks by ID
- **Worker**:
  - 🔐 Securely log in to the system.
  - 📥 View all assigned tasks with rich visual info
  - ▶️ Start and stop tasks with timestamps automatically tracked
  - 🤖 Get AI-generated task breakdowns (subtasks as checkboxes)
  - ☑️ Mark individual subtasks as completed (manager sees live updates)
  - ⏱️ View time spent and expected duration comparison
  - 📤 Submit delay reasons if a task was completed late
  - 📊 See progress bar and completion percentage per task

## 🧱 Tech Stack

- **Backend**: Python + Flask + SQLite
- **Frontend**: Streamlit
- **AI/NLP**: SentenceTransformers (MiniLM), GPT-3.5-turbo via OpenRouter
- **ML Models**: Task duration regression (joblib model), category encoder

## 🖼️ Screenshots

### 🧠 Manager Panel
![Manager](https://github.com/user-attachments/assets/df089e85-c849-4b08-8975-54f3ad48753e)
### 👷 Worker Panel
 ![Worker](https://github.com/user-attachments/assets/7451f793-de86-40d1-9214-e71cddfb5b86)

## ⚙️ How to Run

1. **Clone the Repo**  
   ```bash
   git clone https://github.com/Gokhan-Ergul/smarttask-ai.git
   cd smarttask-ai
