from flask import(
    Blueprint,
    render_template,
    redirect,
    session,
    jsonify,
    make_response
)

from datetime import datetime, timedelta, date

import json
with open("shared/enums.json", "r") as f:
    ENUMS = json.load(f)
    
from scripts.db import db
from scripts.models import Bench, Inspection, InspectionSession, SessionUser, LayoutSnapshot
from routes.auth import login_required
from utils.audit import write_audit
from utils.socketio_instance import socketio
from utils.backup import perform_daily_backup


session_bp = Blueprint("session", __name__)

@session_bp.route("/heartbeat", methods=["POST"])
@login_required
def heartbeat():
    perform_daily_backup()
    
    if "session_id" not in session:
        return jsonify({ "success": False}), 401
    
    user = SessionUser.query.filter_by(session_id=session["session_id"], user_id=session["user_id"]).first()

    if user:
        user.last_seen = datetime.now()
        db.session.commit()

    active_users = SessionUser.query.filter(SessionUser.session_id == session["session_id"], SessionUser.last_seen >= datetime.now() - timedelta(minutes=2)).all()
    socketio.emit("active_users_changed", { "users": [u.user.initials for u in active_users]})

    return jsonify({ "success": True })

@session_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    initials = session.get("initials", "UNKNOWN")

    if "session_id" in session and "user_id" in session:
        user = SessionUser.query.filter_by(session_id=session["session_id"], user_id=session["user_id"]).first()

        if user:
            db.session.delete(user)
            db.session.commit()

    write_audit(initials, "LOGOUT", f"User {initials} logged out")

    session.clear()

    return "", 204


@session_bp.route("/dashboard")
@login_required
def dashboard():
    if "session_id" not in session:
        return redirect("/menu")
     
    is_friday = datetime.today().weekday() == 4

    active_users = (SessionUser.query.filter(SessionUser.session_id == session["session_id"], SessionUser.last_seen >= datetime.now() - timedelta(minutes=2)).all())

    benches = Bench.query.all()
    total_benches = (
        Bench.query
        .filter_by(active=True)
        .count()
    )

    completed_benches = Inspection.query.filter_by(session_id=session["session_id"]).count()
    progress_percent = round((completed_benches / total_benches) * 100) if total_benches else 0
    
    inspections = Inspection.query.filter_by(session_id=session["session_id"]).all()
    
    bench_results = {}
    
    for inspection in inspections:
        bench_results[inspection.bench_id] = (inspection.overall_result)
    
    return render_template(
        "dashboard.html", 
        benches=benches, 
        bench_results=bench_results, 
        is_friday=is_friday, 
        session_id=session["session_id"],
        total_benches=total_benches,
        completed_benches=completed_benches,
        progress_percent=progress_percent,
        active_users=active_users,
        inspection_details={},
        date=datetime.now().strftime(ENUMS["Formatting"]["DATE_FORMAT"])
        )

@session_bp.route("/complete-session", methods=["POST"])
@login_required
def complete_session():
    current = db.session.get(InspectionSession, session["session_id"])
    if not current:
        return jsonify({ "success": False, "message": "Session not found." }), 404

    inspections = Inspection.query.filter_by(session_id=session["session_id"]).count()

    bench_count = Bench.query.count()

    if inspections < bench_count:
        return jsonify({ "success": False, "message": f"{bench_count - inspections} benches remain untested." })

    current.completed_by = session.get("initials")
    current.status = "COMPLETED"
    current.end_time = datetime.now()
    
    write_audit(session.get("initials"), "COMPLETE_SESSION", f"Session {current.id} completed by {session.get('initials')}")
    session.pop("session_id", None)

    return jsonify({ "success": True })

@session_bp.route("/history")
@login_required
def history():
    sessions = (InspectionSession.query.order_by(InspectionSession.date.desc()).all())

    return render_template("history.html", sessions=sessions)

@session_bp.route("/history/<int:session_id>")
@login_required
def view_session(session_id):
    inspection_session = (InspectionSession.query.get_or_404(session_id))
    inspections = Inspection.query.filter_by(session_id=session_id).all()

    bench_results = {}
    inspection_details = {}
    
    for inspection in inspections:
        bench_results[inspection.bench_id] = (inspection.overall_result)
        inspection_details[inspection.bench_id] = {
        "gb_result": inspection.gb_result,
        "ir_result": inspection.ir_result,
        "weekly_result": inspection.weekly_result,
        "overall_result": inspection.overall_result,
        "fail_reason": inspection.fail_reason,
        "comments": inspection.comments
    }
        
    total_benches = Bench.query.count()
    completed_benches = len(inspections)

    progress_percent = round((completed_benches / total_benches) * 100) if total_benches else 0

    layout_snapshot = (
        LayoutSnapshot.query
        .filter_by(session_id=session_id)
        .all()
    )
        
    response = make_response(render_template(
            "history_dashboard.html",
            benches=layout_snapshot,
            bench_results=bench_results,
            inspection_details=inspection_details,
            inspection_session=inspection_session,
            completed_benches=completed_benches,
            total_benches=total_benches,
            progress_percent=progress_percent
        ))
    response.headers["Cache-Control"] = ("no-store, no-cache, must-revalidate, max-age=0")
  
    return response

@session_bp.route("/history/<int:session_id>/delete", methods=["POST"])
@login_required
def delete_session(session_id):
    if not session.get("is_admin"):
        return jsonify({ "success": False }), 403

    inspection_session = (InspectionSession.query.get_or_404(session_id))
    socketio.emit("session_deleted", { "session_id": inspection_session.id })

    Inspection.query.filter_by(session_id=session_id).delete()
    InspectionSession.query.filter_by(id=session_id).delete()
    db.session.commit()

    write_audit(session["initials"], "DELETE_SESSION", f"Session {session_id} deleted")

    
    return jsonify({ "success": True })