from functools import wraps

from datetime import date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

from flask import(
    Blueprint,
    render_template,
    request,
    redirect,
    session
)

from database.db import db
from database.models import InspectionSession, SessionUser, User
import versioning

import json
from pathlib import Path

from datetime import date, datetime

auth_bp = Blueprint("auth", __name__)

START_TIME = datetime.now()

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

@auth_bp.route("/")
def login_page():
    return render_template("login.html")

@auth_bp.route("/start", methods=["POST"])
def start_session():
    initials = request.form["initials"].upper()
    password = request.form["password"]

    auth_user = User.query.filter_by(initials=initials).first()

    if (not auth_user or not check_password_hash(auth_user.password_hash, password)):
        return "Invalid initials or password", 401

    if auth_user.must_change_password:
        session["pending_password_change"] = auth_user.id
        return redirect("/change-password")
    
    session.clear()
    
    session["user_id"] = auth_user.id
    session["initials"] = auth_user.initials
    session["is_admin"] = auth_user.is_admin

    return redirect("/menu")

@auth_bp.route("/change-password")
def change_password_page():
    if "pending_password_change" not in session:
        return redirect("/")

    return render_template("change_password.html")

@auth_bp.route("/change-password", methods=["POST"])
def change_password():
    user_id = session.get("pending_password_change")

    if not user_id:
        return redirect("/")

    password = request.form["password"]
    confirm = request.form["confirm_password"]

    if password != confirm:
        return "Passwords do not match", 400

    user = User.query.get_or_404(user_id)
    user.password_hash = generate_password_hash(password)
    user.must_change_password = False

    db.session.commit()

    session.pop("pending_password_change", None)

    return redirect("/")

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

    return redirect("/dashboard")

@auth_bp.route("/about")
@login_required
def about():
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
        backup_info=backup_info
    )