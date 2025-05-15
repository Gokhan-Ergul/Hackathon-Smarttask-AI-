from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.sqlite import JSON


db = SQLAlchemy()

class AssignedTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assigned_to = db.Column(db.String(50), nullable=False)
    task_name = db.Column(db.String(100), nullable=False)

    summary = db.Column(db.Text, nullable=False)
    priority = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    subcategory = db.Column(db.String(50), nullable=False)

    expected_duration = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="not_started")
    start_time = db.Column(db.String(100))
    end_time = db.Column(db.String(100))
    actual_duration = db.Column(db.Float)
    delay_reason = db.Column(db.Text)
    performance_status = db.Column(db.String(20))

    task_plan = db.Column(db.Text)
    task_steps = db.Column(JSON)


from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

