from functools import wraps

from datetime import date

from flask import(
    Blueprint,
    render_template,
    request,
    redirect,
    session
)

from database.db import db
from database.models import InspectionSession, SessionUser

from datetime import date, datetime

auth_bp = Blueprint("auth", __name__)

def valid_session_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):
        if "session_id" not in session or "initials" not in session:
            return redirect("/")
        
        return f(*args, **kwargs)
    
    return decorated
        
@auth_bp.route("/")
def login_page():
    return render_template("login.html")

@auth_bp.route("/start", methods=["POST"])
def start_session():
    existing_user = session.get("initials")

    initials = request.form["initials"].upper()
    if existing_user and existing_user != initials:
        return f"Already logged in as {existing_user}. Please log out before switching user.", 403
            
    today_session = InspectionSession.query.filter_by(date=date.today(), status="IN_PROGRESS").first()

    if today_session:
        user = SessionUser.query.filter_by(session_id=today_session.id, initials=initials).first()

        if not user:
            db.session.add(SessionUser(session_id=today_session.id, initials=initials, last_seen=datetime.now()))

        db.session.commit()
            
        session["session_id"] = today_session.id
        session["initials"] = initials
        
        return redirect("/dashboard")
    
    elif not today_session:
        new_session = InspectionSession(initials=initials, date=date.today(), status="IN_PROGRESS")
        
        db.session.add(new_session)
        db.session.commit()

        db.session.add(SessionUser(session_id=new_session.id, initials=initials, last_seen=datetime.now()))
        db.session.commit()

        session["session_id"] = new_session.id
        session["initials"] = initials
        
        return redirect("/dashboard")