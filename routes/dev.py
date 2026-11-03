from flask import Blueprint, redirect, render_template, current_app
from pathlib import Path
from routes.auth import login_required, developer_required
from utils.backup import backup
from scripts.models import *

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
        routes.append({ "path": str(rule), "methods": ", ".join(sorted(rule.methods)), "endpoint": rule.endpoint})

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
    stats = {
        "users": User.query.count(),
        "enabled_users": User.query.filter_by(is_enabled=True).count(),
        "disabled_users": User.query.filter_by(is_enabled=False).count(),
        "sessions": InspectionSession.query.count(),
        "completed_sessions": InspectionSession.query.filter_by(status="COMPLETED").count(),
        "audits": AuditLog.query.count(),
        "bench_inspections": Inspection.query.count()
    }

    return render_template("dev/stats.html", stats=stats)