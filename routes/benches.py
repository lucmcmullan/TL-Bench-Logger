from flask import(
    Blueprint,
    jsonify,
    request,
    session
)

from routes.auth import login_required
from database.db import db
from datetime import date, datetime, timedelta
from database.models import Inspection, InspectionSession, BenchLock, Bench

from socketio_instance import socketio

bench_bp = Blueprint("bench", __name__)

@bench_bp.route("/lock-bench", methods=["POST"])
@login_required
def lock_bench():
    if "initials" not in session:
        return jsonify({ "success": False, "message": "You must be logged in to access this."}), 401
    
    BenchLock.query.filter(BenchLock.locked_at < (datetime.now() - timedelta(minutes=2))).delete()
    db.session.commit()
    
    data = request.get_json()

    if not data or "bench_id" not in data:
        return jsonify({ "success": False, "message": "bench_id missing" }), 400

    existing = BenchLock.query.filter_by(bench_id=data["bench_id"]).first()

    if existing:
        if existing.locked_by == session["initials"]:
            existing.locked_at = datetime.now()
            db.session.commit()

            return jsonify ({ "success": True })
        
        if existing.locked_at < (datetime.now() - timedelta(minutes=2)):
            db.session.delete(existing)
            db.session.commit()
        else:
            return jsonify({ "success": False, "locked_by": existing.locked_by})

    lock = BenchLock(bench_id=data["bench_id"], locked_by=session["initials"], locked_at=datetime.now())

    db.session.add(lock)
    db.session.commit()
    
    socketio.emit("lock_changed", {"bench_id": data["bench_id"], "locked": True})

    return jsonify({ "success": True })

@bench_bp.route("/unlock-bench", methods=["POST"])
@login_required
def unlock_bench():
    data = request.json

    lock = BenchLock.query.filter_by(bench_id=data["bench_id"]).first()

    if lock:
        db.session.delete(lock)
        db.session.commit()

        socketio.emit("lock_changed", {"bench_id": data["bench_id"], "locked": False})
        
        return jsonify({ "success": True})

    return jsonify({ "success": False, "message": "No lock found"})

@bench_bp.route("/lock-status")
@login_required
def lock_status():
    locks = BenchLock.query.all()

    return jsonify([{ "bench_id": l.bench_id, "locked_by": l.locked_by } for l in locks])
 
@bench_bp.route("/inspect", methods=["POST"])
@login_required
def inspect_bench():
    data = request.json

    results = [data.get("gb_result"), data.get("ir_result"), data.get("weekly_result")]

    overall = "FAIL" if "FAIL" in results else "PASS"

    inspection = Inspection.query.filter_by(
        session_id=session["session_id"], 
        bench_id=data["bench_id"]).first()
    
    failed = (overall == "FAIL")
    
    if failed and not data.get("fail_reason"):
        return jsonify({ "success": False, "message": "Failure reason required." }), 400
    
    if inspection:
        inspection.gb_result = data["gb_result"]
        inspection.ir_result = data["ir_result"]
        inspection.weekly_result = data.get("weekly_result")
        inspection.overall_result = overall
        inspection.fail_reason = data.get("fail_reason")
        inspection.comments = data.get("comments")
    else:
        inspection = Inspection(
            session_id=session["session_id"],
            bench_id=data["bench_id"],
            gb_result=data["gb_result"],
            ir_result=data["ir_result"],
            weekly_result=data.get("weekly_result"),
            overall_result=overall,
            fail_reason=data.get("fail_reason"),
            comments=data.get("comments")
        )

        db.session.add(inspection)
        
    lock = BenchLock.query.filter_by(bench_id=data["bench_id"]).first()

    if lock:
        db.session.delete(lock)

    db.session.commit()

    socketio.emit("bench_updated", {"bench_id": data["bench_id"], "result": overall})
    socketio.emit("lock_changed", {"bench_id": data["bench_id"], "locked": False})

    return jsonify({ "success": True, "overall": overall })

@bench_bp.route("/inspection-status")
@login_required
def inspection_status():
    inspections = Inspection.query.join(InspectionSession).filter(InspectionSession.date == date.today())
    
    return jsonify([{ "bench_id": i.bench_id, "result": i.overall_result } for i in inspections])

@bench_bp.route("/reset-inspection", methods=["POST"])
@login_required
def reset_inspection():
    data = request.get_json()

    inspection = Inspection.query.filter_by(session_id=session["session_id"], bench_id=data["bench_id"]).first()

    if inspection:
        db.session.delete(inspection)

        db.session.commit()

        return jsonify({ "success": True })

@bench_bp.route("/progress")
@login_required
def progress():
    total_benches = Bench.query.count()

    completed_benches = Inspection.query.filter_by(session_id=session["session_id"]).count()

    progress_percent = round((completed_benches / total_benches) * 100) if total_benches else 0

    return jsonify({ "completed": completed_benches, "total": total_benches, "percent": progress_percent })