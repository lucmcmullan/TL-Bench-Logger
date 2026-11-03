from datetime import datetime

from scripts.db import db

from constants import defaults

class Bench(db.Model):
    __tablename__ = "benches"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    x = db.Column(db.Integer, nullable=True)
    y = db.Column(db.Integer, nullable=True)
    active = db.Column(db.Boolean, default=defaults["BenchActive"])
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
    start_time = db.Column(db.DateTime, default=datetime.now())
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default=defaults["InspectionSessionStatus"])
    duration_seconds = db.Column(db.Integer)
    inspections = db.relationship("Inspection", backref="session", lazy=True)
    completed_by = db.Column(db.String(10), nullable=True)

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
    timestamp = db.Column(db.DateTime, default=datetime.now())

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    initials = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_enabled = db.Column(db.Boolean, nullable=False, default=True)
    must_change_password = db.Column(db.Boolean, default=True)
    password_reset_at = db.Column(db.DateTime)

class SessionUser(db.Model):
    __tablename__ = "session_users"
    user = db.relationship("User", backref="session_entries")

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    last_seen = db.Column(db.DateTime)
    
class AuditLog(db.Model):
    __tablename__ = "audit_log"
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    user_initials = db.Column(db.String(10), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(500), nullable=False)