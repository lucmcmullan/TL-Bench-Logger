from flask import Blueprint, redirect, render_template, current_app, session
from pathlib import Path
from datetime import datetime
from routes.auth import login_required, developer_required
from utils.audit import write_audit
from utils.backup import backup
from scripts.models import *
from utils.socketio_instance import socketio

import json
with open("shared/enums.json", "r") as f:
    ENUMS = json.load(f)

dev_bp = Blueprint("dev", __name__)


@dev_bp.route("/dev")
@login_required
@developer_required
def dev_home():
    return render_template("dev/dev.html")


@dev_bp.route("/dev/routes")
@login_required
@developer_required
def dev_routes():
    routes = []

    for rule in current_app.url_map.iter_rules():
        routes.append({"path": str(rule), "methods": ", ".join(
            sorted(rule.methods)), "endpoint": rule.endpoint})

    return render_template("dev/routes.html", routes=sorted(routes, key=lambda x: x["path"]))


@dev_bp.route("/dev/backups")
@login_required
@developer_required
def dev_backups():
    backups = []
    backup_dir = Path("data/backups")

    if backup_dir.exists():
        backups = sorted(backup_dir.glob("*.db"), reverse=True)

    return render_template("dev/backups.html", backups=backups)


@dev_bp.route("/dev/create-backup", methods=["POST"])
@login_required
@developer_required
def create_backup():
    backup("Manual")

    return redirect("/dev/backups")


@dev_bp.route("/dev/stats")
@login_required
@developer_required
def dev_stats():
    db_file = Path("data/app.db")

    db_size_mb = 0

    if db_file.exists():
        db_size_mb = round(db_file.stat().st_size / 1024 / 1024, 2)

    stats = {
        "users": User.query.count(),
        "enabled_users": User.query.filter_by(is_enabled=True).count(),
        "disabled_users": User.query.filter_by(is_enabled=False).count(),
        "sessions": InspectionSession.query.count(),
        "completed_sessions": InspectionSession.query.filter_by(status="COMPLETED").count(),
        "audits": AuditLog.query.count(),
        "bench_inspections": Inspection.query.count(),
        "db_size_mb": db_size_mb,
    }

    return render_template("dev/stats.html", stats=stats)


@dev_bp.route("/dev/test-routes")
@login_required
@developer_required
def test_routes():
    results = []

    with current_app.test_client() as client:
        for rule in current_app.url_map.iter_rules():
            if rule.endpoint == "static":
                continue

            path = str(rule)

            if "<" in path:
                continue

            try:
                if "GET" in rule.methods:
                    response = client.get(path)
                elif "POST" in rule.methods:
                    response = client.post(path)

                results.append({"route": path, "status": response.status_code})

            except Exception as e:
                results.append({"route": path, "status": f"ERROR: {e}"})

    return render_template("dev/route_test.html", results=results)


@dev_bp.route("/dev/pass-all-benches")
@login_required
@developer_required
def pass_all_benches():
    current = (InspectionSession.query.filter_by(
        status=ENUMS["InspectionSessionStatus"]["IN_PROGRESS"]).first())
    if not current:
        return redirect("/dashboard")

    benches = Bench.query.filter_by(active=True).all()

    for bench in benches:
        inspection = Inspection.query.filter_by(
            session_id=current.id, bench_id=bench.id).first()

        if inspection:
            inspection.ir_result = "PASS"
            inspection.gb_result = "PASS"
            inspection.weekly_result = "PASS"
            inspection.overall_result = "PASS"
            inspection.fail_reason = None
            inspection.comments = "This bench was passed by a developer override."

        else:

            db.session.add(
                Inspection(
                    session_id=current.id,
                    bench_id=bench.id,
                    ir_result="PASS",
                    gb_result="PASS",
                    weekly_result="PASS",
                    overall_result="PASS",
                    comments="This bench was passed by a developer override.",
                    timestamp=datetime.now()
                )
            )

    db.session.commit()

    socketio.emit("inspection_refresh", {"action": "pass_all"})
    write_audit(session["initials"], "DEV_ACTION", "Pass All Benches")

    return redirect("/dashboard")


@dev_bp.route("/dev/fail-all-benches")
@login_required
@developer_required
def fail_all_benches():
    current = (InspectionSession.query.filter_by(
        status=ENUMS["InspectionSessionStatus"]["IN_PROGRESS"]).first())
    if not current:
        return redirect("/dashboard")

    benches = Bench.query.filter_by(active=True).all()

    for bench in benches:
        inspection = Inspection.query.filter_by(
            session_id=current.id, bench_id=bench.id).first()

        if inspection:
            inspection.ir_result = "FAIL"
            inspection.gb_result = "FAIL"
            inspection.weekly_result = "FAIL"
            inspection.overall_result = "FAIL"
            inspection.fail_reason = "Developer Override"
            inspection.comments = "This bench was failed by a developer override."

        else:

            db.session.add(
                Inspection(
                    session_id=current.id,
                    bench_id=bench.id,
                    ir_result="FAIL",
                    gb_result="FAIL",
                    weekly_result="FAIL",
                    overall_result="FAIL",
                    fail_reason="Developer Override",
                    comments="This bench was failed by a developer override.",
                    timestamp=datetime.now()
                )
            )

    db.session.commit()

    socketio.emit("inspection_refresh", {"action": "fail_all"})
    write_audit(session["initials"], "DEV_ACTION", "Fail All Benches")

    return redirect("/dashboard")


@dev_bp.route("/dev/reset-all-benches")
@login_required
@developer_required
def reset_all_benches():
    current = (InspectionSession.query.filter_by(
        status=ENUMS["InspectionSessionStatus"]["IN_PROGRESS"]).first())

    if not current:
        return redirect("/dashboard")

    Inspection.query.filter_by(session_id=current.id).delete()

    db.session.commit()

    write_audit(session["initials"], "DEV_ACTION", "Reset All Benches")

    return redirect("/dashboard")
