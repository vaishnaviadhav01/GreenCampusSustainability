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
