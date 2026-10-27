from flask import(
    Blueprint,
    render_template,
    redirect,
    session,
    jsonify
)

from datetime import datetime, timedelta, UTC
from constants import FACTORY_LAYOUT
from database.db import db
from database.models import Bench, Inspection, InspectionSession, SessionUser
from routes.auth import valid_session_required
from socketio_instance import socketio

from constants import NO_CELL_PREFIX

session_bp = Blueprint("session", __name__)

@session_bp.route("/heartbeat", methods=["POST"])
@valid_session_required
def heartbeat():
    if "session_id" not in session:
        return jsonify({ "success": False}), 401
    
    user = SessionUser.query.filter_by(session_id=session["session_id"], user_id=session["user_id"]).first()

    if user:
        user.last_seen = datetime.now(UTC)
        db.session.commit()

    active_users = SessionUser.query.filter(SessionUser.session_id == session["session_id"], SessionUser.last_seen >= datetime.now(UTC) - timedelta(minutes=2)).all()
    socketio.emit("active_users_changed", { "users": [u.user.initials for u in active_users]})

    return jsonify({ "success": True })

@session_bp.route("/logout", methods=["POST"])
def logout():
    if "session_id" in session and "user_id" in session:
        user = SessionUser.query.filter_by(session_id=session["session_id"], user_id=session["user_id"]).first()

        if user:
            db.session.delete(user)
            db.session.commit()

        session.clear()
        
        return "", 204


@session_bp.route("/dashboard")
@valid_session_required
def dashboard():
    is_friday = datetime.today().weekday() == 4

    active_users = (SessionUser.query.filter(SessionUser.session_id == session["session_id"], SessionUser.last_seen >= datetime.now(UTC) - timedelta(minutes=2)).all())

    total_benches = Bench.query.count()

    completed_benches = Inspection.query.filter_by(session_id=session["session_id"]).count()
    progress_percent = round((completed_benches / total_benches) * 100) if total_benches else 0
    
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
        total_benches=total_benches,
        completed_benches=completed_benches,
        progress_percent=progress_percent,
        active_users=active_users,
        no_cell_prefix=NO_CELL_PREFIX)

@session_bp.route("/complete-session", methods=["POST"])
@valid_session_required
def complete_session():
    current = InspectionSession.query.get(session["session_id"])

    inspections = Inspection.query.filter_by(session_id=session["session_id"]).count()

    bench_count = Bench.query.count()

    if inspections < bench_count:
        return jsonify({ "success": False, "message": f"{bench_count - inspections} benches remain untested." })
    
    current.status = "COMPLETED"
    current.end_time = datetime.now(UTC)
    
    db.session.commit()

    session.clear()

    return jsonify({ "success": True })