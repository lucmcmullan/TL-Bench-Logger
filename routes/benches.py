from flask import(
    Blueprint,
    jsonify,
    request,
    session
)

from database.db import db
from datetime import date, datetime, timedelta
from database.models import Inspection, InspectionSession, BenchLock

bench_bp = Blueprint("bench", __name__)

@bench_bp.route("/lock-bench", methods=["POST"])
def lock_bench():
    data = request.json

    existing = BenchLock.query.filter_by(bench_id=data["bench_id"]).first()

    if existing:
        if existing.locked_at < (datetime.now() - timedelta(minutes=2)):
            db.session.delete(existing)
            db.session.commit()
        else:
            return jsonify({ "success": False, "locked_by": existing.locked_by})

    lock = BenchLock(bench_id=data["bench_id"], locked_by=session["initials"], locked_at=datetime.now())

    db.session.add(lock)
    db.session.commit()

    return jsonify({ "success": True })

@bench_bp.route("/lock-status")
def lock_status():
    locks = BenchLock.query.all()

    return jsonify([{ "bench_id": l.bench_id, "locked_by": l.locked_by } for l in locks])

@bench_bp.route("/unlock-bench", methods=["POST"])
def unlock_bench():
    data = request.json

    lock = BenchLock.query.filter_by(bench_id=data["bench_id"]).first()

    if lock:
        db.session.delete(lock)
        db.session.commit()

        return jsonify({ "success": True})

    return jsonify({ "success": False, "message": "No lock found"})
    
@bench_bp.route("/inspect", methods=["POST"])
def inspect_bench():
    data = request.json

    overall = "PASS"

    if data["gb_result"] == "FAIL" or data["ir_result"] == "FAIL" or data.get("weekly_result") == "FAIL":
        overall = "FAIL"

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

    return jsonify({ "success": True, "overall": overall })

@bench_bp.route("/inspection-status")
def inspection_status():
    inspections = Inspection.query.join(InspectionSession).filter(InspectionSession.date == date.today())
    
    return jsonify([{ "bench_id": i.bench_id, "result": i.overall_result } for i in inspections])