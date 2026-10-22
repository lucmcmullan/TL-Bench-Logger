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

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def login_page():
    return render_template("login.html")

@auth_bp.route("/start", methods=["POST"])
def start_session():
    initials = request.form["initials"].upper()
    
    candidate_session = (InspectionSession.query.filter_by(initials=initials, status="IN_PROGRESS").all())
    
    existing_session = None
    
    for s in candidate_session:
        inspection_count = Inspection.query.filter_by(session_id=s.id).count()
        
        if inspection_count > 0:
            existing_session = s
            break
        
    if existing_session:
        session["session_id"] = existing_session.id
        session["initials"] = initials
        
        return redirect(url_for("session.dashboard"))
    
    elif not existing_session:
        new_session = InspectionSession(initials=initials, date=date.today(), status="IN_PROGRESS")
        
        db.session.add(new_session)
        db.session.commit()
        
        session["session_id"] = new_session.id
        session["initials"] = initials
        
        return redirect(url_for("session.dashboard"))