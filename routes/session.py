from flask import(
    Blueprint,
    render_template,
    redirect,
    session,
    jsonify
)

from datetime import datetime

from database.db import db
from database.models import Bench, Inspection, InspectionSession

session_bp = Blueprint("session", __name__)

@session_bp.route("/dashboard")
def dashboard():
    is_friday = datetime.today().weekday() == 3

    if "session_id" not in session:
        return redirect("/")
    
    benches = Bench.query.all()
    
    inspections = Inspection.query.filter_by(session_id=session["session_id"]).all()
    
    bench_results = {}
    
    for inspection in inspections:
        bench_results[inspection.bench_id] = (inspection.overall_result)
    
    return render_template("dashboard.html", benches=benches, bench_results=bench_results, is_friday=is_friday)

@session_bp.route("/complete-session", methods=["POST"])
def complete_session():
    current = InspectionSession.query.get(session["session_id"])
    
    current.status = "COMPLETED"
    current.end_time = datetime.now()
    
    db.session.commit()
    
    return jsonify({ "success": True })