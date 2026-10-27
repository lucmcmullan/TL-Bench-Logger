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

from datetime import date, datetime, UTC

auth_bp = Blueprint("auth", __name__)

def valid_session_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "session_id" not in session or "initials" not in session or "user_id" not in session:
            return redirect("/")
        
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect("/dashboard")

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
    
    existing_user = session.get("initials")

    if existing_user and existing_user != initials:
        return f"Already logged in as {existing_user}. Please log out before switching user.", 403

    inspection_session = (InspectionSession.query.filter_by(date=date.today(), status="IN_PROGRESS").first())

    if inspection_session:
        session_user = SessionUser.query.filter_by(session_id=inspection_session.id, user_id=auth_user.id).first()

        if not session_user:
            active_users = SessionUser.query.filter(SessionUser.session_id == inspection_session.id, SessionUser.last_seen >= (datetime.now(UTC) - timedelta(minutes=2))).all()

            return render_template(
                "join_session.html",
                active_users=active_users,
                session_id=inspection_session.id,
                user_id=auth_user.id,
                initials=auth_user.initials
            )
    elif not inspection_session:
        inspection_session = InspectionSession(initials=initials, date=date.today(), status="IN_PROGRESS")

        db.session.add(inspection_session)
        db.session.commit()

    session["user_id"] = auth_user.id
    session["session_id"] = inspection_session.id
    session["initials"] = auth_user.initials
    session["is_admin"] = auth_user.is_admin

    return redirect("/dashboard")

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

@auth_bp.route("/join-session", methods=["POST"])
def join_session():
    user_id = request.form["user_id"]

    auth_user = User.query.get_or_404(user_id)

    inspection_session = (InspectionSession.query.filter_by(date=date.today(), status="IN_PROGRESS").first())
    session_user = SessionUser.query.filter_by(session_id=inspection_session.id, user_id=auth_user.id).first()

    if not session_user:
        db.session.add(SessionUser(session_id=inspection_session.id, user_id=auth_user.id, last_seen=datetime.now(UTC)))
        db.session.commit()

    session["user_id"] = auth_user.id
    session["session_id"] = inspection_session.id
    session["initials"] = auth_user.initials
    session["is_admin"] = auth_user.is_admin

    return redirect("/dashboard")