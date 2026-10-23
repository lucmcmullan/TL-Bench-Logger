from datetime import datetime

from database.db import db


class Bench(db.Model):
    __tablename__ = "benches"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    x = db.Column(db.Integer, nullable=True)
    y = db.Column(db.Integer, nullable=True)
    active = db.Column(db.Boolean, default=True)
    tested_by = db.Column(db.String(10), nullable=True)
    last_modified = db.Column(db.DateTime)
    inspections = db.relationship("Inspection", backref="bench", lazy=True)

class BenchLock(db.Model):
    __tablename__ = "bench_locks"

    bench_id = db.Column(db.Integer, db.ForeignKey("benches.id"), primary_key=True)
    locked_by = db.Column(db.String(10), nullable=False)
    locked_at = db.Column(db.DateTime, nullable=False)
    
class InspectionSession(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    initials = db.Column(db.String(10), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    active_users = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="IN_PROGRESS")
    duration_seconds = db.Column(db.Integer)
    inspections = db.relationship("Inspection", backref="session", lazy=True)


class Inspection(db.Model):
    __tablename__ = "inspections"
    __table_args__ = (db.UniqueConstraint("session_id", "bench_id", name="uq_session_bench"),)

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"), nullable=False)
    bench_id = db.Column(db.Integer, db.ForeignKey("benches.id"), nullable=False)
    ir_result = db.Column(db.String(10), nullable=False)
    gb_result = db.Column(db.String(10), nullable=False)
    weekly_result = db.Column(db.String(10))
    overall_result = db.Column(db.String(10))
    fail_reason = db.Column(db.String(255))
    comments = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class SessionUser(db.Model):
    __tablename__ = "session_users"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"))
    initials = db.Column(db.String(10), nullable=False)
    last_seen = db.Column(db.DateTime)