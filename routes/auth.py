from datetime import date

from flask import(
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from database.db import db
from database.models import InspectionSession, Inspection

from datetime import date

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def login_page():
    return render_template("login.html")

@auth_bp.route("/start", methods=["POST"])
def start_session():
    initials = request.form["initials"].upper()
    today_session = InspectionSession.query.filter_by(date=date.today(), status="IN_PROGRESS").first()

    if today_session:
        active_users = []

        if today_session.active_users:
            active_users = (today_session.active_users.split(", "))
        if initials not in active_users:
            active_users.append(initials)
            today_session.active_users = ", ".join(active_users)
            db.session.commit()
            
        session["session_id"] = today_session.id
        session["initials"] = initials
        
        return redirect("/dashboard")
    
    elif not today_session:
        new_session = InspectionSession(initials=initials, date=date.today(), status="IN_PROGRESS")
        
        db.session.add(new_session)
        db.session.commit()
        
        session["session_id"] = new_session.id
        session["initials"] = initials
        
        return redirect("/dashboard")