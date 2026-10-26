from functools import wraps

from datetime import date
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

from datetime import date, datetime

auth_bp = Blueprint("auth", __name__)

def valid_session_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "session_id" not in session or "initials" not in session or "user_id" not in session:
            return redirect("/")
        
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

    existing_user = session.get("initials")

    if existing_user and existing_user != initials:
        return f"Already logged in as {existing_user}. Please log out before switching user.", 403)

    inspection_session = (InspectionSession.query.filter_by(date=date.today(), status="IN_PROGRESS").first())

    if not inspection_session: 
        inspection_session = InspectionSession(initials=initials, date=date.today(), status="IN_PROGRESS")

        db.session.add(inspection_session)
        db.session.commit()

    session_user = SessionUser.query.filter_by(session_id=inspection_session.id, user_id=auth_user.id).first()

    if not session_user:
        db.session.add(SessionUser(session_id=inspection_session.id, user_id=auth_user.id, last_seen=datetime.now()))
        db.session.commit()

    session["user_id"] = auth_user.id
    session["session_id"] = inspection_session.id
    session["initials"] = auth_user.initials
    session["is_admin"] = auth_user.is_admin

    return redirect("/dashboard")