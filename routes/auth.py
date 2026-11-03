from functools import wraps

from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash

from utils.audit import write_audit
from utils.uptime import UPTIME_FILE, init_uptime
import atexit

from flask import(
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    flash,
    abort
)

from scripts.db import db
from scripts.models import InspectionSession, SessionUser, User
import utils.versioning as versioning
import time
import json
import psutil
from pathlib import Path

from datetime import date, datetime

auth_bp = Blueprint("auth", __name__)

START_TIME =init_uptime()

@atexit.register
def save_shutdown_time():
    if not UPTIME_FILE.exists():
        return

    data = json.loads(UPTIME_FILE.read_text())
    data["last_shutdown"] = (datetime.now().isoformat())
    UPTIME_FILE.write_text(json.dumps(data, indent=4))
    
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        if "user_id" not in session:
            return redirect("/")

        return f(*args, **kwargs)

    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect("/main")

        return f(*args, **kwargs)
    return decorated

def developer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        if session.get("initials") != "LM":
            abort(403)

        return f(*args, **kwargs)

    return decorated

@auth_bp.route("/")
def login_page():
    return render_template("login.html")

@auth_bp.route("/start", methods=["POST"])
def start_session():
    initials = request.form.get("initials")
    password = request.form.get("password")

    if not initials or not password:
        return "Missing initials or password", 400

    initials = initials.upper()

    auth_user = User.query.filter_by(initials=initials).first()

    if not auth_user:
        return "Invalid initials or password", 401

    if not check_password_hash(auth_user.password_hash, password):
        return "Invalid initials or password", 401

    if not auth_user.is_enabled:
        return "Account is disabled. Please contact an administrator.", 403

    session.clear()

    session["user_id"] = auth_user.id
    session["initials"] = auth_user.initials
    session["is_admin"] = auth_user.is_admin

    write_audit(session["initials"], "LOGIN", f"User {session['initials']} logged in")

    return redirect("/menu")


@auth_bp.route("/change-password", methods=["POST"])
def change_password():
    initials = request.form.get("initials")
    password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if not initials:
        return "Missing initials", 400

    if not password:
        return "Missing password", 400

    if not confirm_password:
        return "Missing confirmation password", 400

    if password != confirm_password:
        flash("Passwords do not match.", "error")
        return redirect("/")

    user = User.query.filter_by(
        initials=initials
    ).first_or_404()

    user.password_hash = generate_password_hash(password)

    user.must_change_password = False

    db.session.commit()

    session.clear()

    session["user_id"] = user.id
    session["initials"] = user.initials
    session["is_admin"] = user.is_admin

    write_audit(
        user.initials,
        "PASSWORD_CHANGE",
        f"User {user.initials} changed password"
    )

    return redirect("/menu")

@auth_bp.route("/menu")
@login_required
def menu():
    completed_session = (InspectionSession.query.filter_by(date=date.today(), status="COMPLETED").first())

    active_session = (InspectionSession.query.filter_by(date=date.today(), status="IN_PROGRESS").first())

    return render_template("menu.html", completed_session=completed_session, active_session=active_session)

@auth_bp.route("/join-or-start-session", methods=["POST"])
@login_required
def join_or_start_session():
    completed_session = (InspectionSession.query.filter_by(date=date.today(), status="COMPLETED").first())

    if completed_session:
        return "A session has already been completed today", 403

    inspection_session = (InspectionSession.query.filter_by(date=date.today(), status="IN_PROGRESS").first())

    if not inspection_session:
        inspection_session = InspectionSession(initials=session["initials"], date=date.today(), status="IN_PROGRESS")

        db.session.add(inspection_session)

    session_user = SessionUser.query.filter_by(session_id=inspection_session.id, user_id=session["user_id"]).first()

    if not session_user:
        db.session.add(SessionUser(session_id=inspection_session.id, user_id=session["user_id"], last_seen=datetime.now()))

        db.session.commit()

    session["session_id"] = inspection_session.id

    write_audit(session["initials"], "START_SESSION", f"User {session['initials']} joined session {inspection_session.id}")

    return redirect("/dashboard")

@auth_bp.route("/about")
@login_required
def about():
    db_status = "Online"
    try:
        User.query.first()
    except Exception:
        db_status = "Offline"

    memory = psutil.virtual_memory()

    system_health = {
        "db_status": db_status,
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_used_mb": round(memory.used / 1024 / 1024),
        "memory_total_mb": round(memory.total / 1024 / 1024),
        "memory_percent": memory.percent,
        "active_users": SessionUser.query.count()
    }

    backup_info = {"filename": "None", "backup_type": "Unknown", "created_at": "Never"}

    meta_file = Path("data/backups/_last_backup.json")

    if meta_file.exists():
        with open(meta_file) as f:
            backup_info = json.load(f)

    uptime_seconds = int((datetime.now() - START_TIME).total_seconds())

    return render_template(
        "about.html",
        version=versioning.VERSION,
        build_date=versioning.BUILD_DATE,
        build_number=versioning.BUILD_NUMBER,
        uptime_seconds=uptime_seconds,
        backup_info=backup_info,
        system_health=system_health
    )

@auth_bp.route("/check-user/<initials>")
def check_user(initials):
    user = User.query.filter_by(initials=initials.upper()).first()

    return { "exists": user is not None, "must_change_password": user.must_change_password if user else False }