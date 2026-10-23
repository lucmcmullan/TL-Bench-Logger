from flask import(
    Blueprint,
    render_template,
    redirect,
    session,
    jsonify
)

from datetime import datetime, timedelta

from factory import FACTORY_LAYOUT
from database.db import db
from database.models import Bench, Inspection, InspectionSession, SessionUser

session_bp = Blueprint("session", __name__)

@session_bp.route("/heartbeat", methods=["POST"])
def heartbeat():
    if "session_id" not in session:
        return jsonify({ "success": False}), 401
    
    user = SessionUser.query.filter_by(session_id=session["session_id"], initials=session["initials"]).first()

    if user:
        user.last_seen = datetime.now()
        db.session.commit()

    return jsonify({ "success": True })

@session_bp.route("/dashboard")
def dashboard():
    is_friday = datetime.today().weekday() == 4
    active_users = (
        SessionUser.query.filter(
            SessionUser.session_id == session["session_id"], 
            SessionUser.last_seen >= datetime.now() - timedelta(minutes=2)).all()
            )
    
    if "session_id" not in session:
        return redirect("/")
    
    benches = Bench.query.all()
    
    inspections = Inspection.query.filter_by(session_id=session["session_id"]).all()
    
    bench_results = {}
    
    for inspection in inspections:
        bench_results[inspection.bench_id] = (inspection.overall_result)
    
    return render_template(
        "dashboard.html", 
        layout=FACTORY_LAYOUT, 
        bench_results=bench_results, 
        is_friday=is_friday, 
        session_id=session["session_id"],
        active_users=active_users)

@session_bp.route("/complete-session", methods=["POST"])
def complete_session():
    current = InspectionSession.query.get(session["session_id"])
    
    current.status = "COMPLETED"
    current.end_time = datetime.now()
    
    db.session.commit()
    
    return jsonify({ "success": True })