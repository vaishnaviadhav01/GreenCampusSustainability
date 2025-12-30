from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# ---------------- USER MODEL (EXISTING - UNCHANGED) ----------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(10), nullable=False)


# ---------------- RESOURCE USAGE MODEL (NEW) ----------------
class ResourceUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    date = db.Column(db.Date, nullable=False, unique=True)

    electricity = db.Column(db.Float, nullable=False)  # kWh
    water = db.Column(db.Float, nullable=False)        # Liters
    waste = db.Column(db.Float, nullable=False)        # Kg

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ResourceUsage {self.date}>"
    



# ---------------- QUIZ MODELS ----------------

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # ✅ relationships
    questions = db.relationship(
        "QuizQuestion",
        backref="quiz",
        cascade="all, delete-orphan"
    )
    results = db.relationship(
        "QuizResult",
        backref="quiz",
        cascade="all, delete-orphan"
    )


class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    question = db.Column(db.String(500), nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)


class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)