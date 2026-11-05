from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    flash,
    jsonify
)

from werkzeug.security import generate_password_hash

from scripts.db import db
from scripts.models import AuditLog, Bench, User

from datetime import datetime
from utils.audit import write_audit
from utils.socketio_instance import socketio
from routes.auth import login_required, admin_required

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/users")
@login_required
@admin_required
def manage_users():
    users = User.query.order_by(User.initials).all()

    return render_template("admin/users.html", users=users)

@admin_bp.route("/admin/users/create", methods=["POST"])
@login_required
@admin_required
def create_user():
    initials = request.form["initials"].upper()
    name = request.form["name"]
    password = request.form["password"]

    existing = User.query.filter_by(initials=initials).first()

    if existing:
        flash("User already exists.", "error")
        return redirect("/admin/users")

    user = User(initials=initials, name=name, password_hash=generate_password_hash(password), is_admin=False, must_change_password=True)

    db.session.add(user)
    db.session.commit()

    write_audit(session["initials"], "CREATE_USER", f"User created: {initials}")

    return redirect("/admin/users")

@admin_bp.route("/admin/users/reset-password/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)

    user.password_hash = generate_password_hash(user.initials)
    user.must_change_password = True
    user.password_reset_at = datetime.now()

    db.session.commit()

    flash(f"Password for user {user.initials} has been reset.", "success")
    write_audit(session["initials"], "RESET_PASSWORD", f"Password reset for user: {user.initials}")

    return redirect("/admin/users")

@admin_bp.route("/admin/users/toggle-admin/<int:user_id>")
@login_required
@admin_required
def toggle_admin(user_id):
    if user_id == session["user_id"]:
        flash(f"You cannot remove your own admin rights.", "error")
        return redirect("/admin/users")
    elif user_id == 1:
        flash(f"You cannot remove admin rights from the developer.", "error")
        return redirect("/admin/users")

    user = User.query.get_or_404(user_id)
    user.is_admin = (not user.is_admin)
    db.session.commit()

    write_audit(session["initials"], "TOGGLE_ADMIN", f"Admin rights toggled for user: {user.initials}")

    return redirect("/admin/users")

@admin_bp.route("/admin/users/toggle-enabled/<int:user_id>")
@login_required
@admin_required
def toggle_enabled(user_id):
    if user_id == session["user_id"]:
        flash(f"You cannot disable your own account.", "error")
        return redirect("/admin/users")
    elif user_id == 1:
            flash(f"You cannot disable the developer's account.", "error")
            return redirect("/admin/users")
    
    user = User.query.get_or_404(user_id)
    user.is_enabled = (not user.is_enabled)
    db.session.commit()

    write_audit(session["initials"], "USER_STATUS", f"Enabled status toggled for user: {user.initials}")

    return redirect("/admin/users")

@admin_bp.route("/admin/audit-log")
@login_required
@admin_required
def audit_log():
    logs = (AuditLog.query.order_by(AuditLog.timestamp.desc()).all())
    audit_text = "\n".join(f"{log.timestamp:%d/%m/%Y %H:%M:%S} - {log.event_type} - {log.user_initials} - {log.message}" for log in logs)

    return render_template("/admin/audit_log.html", audit_text=audit_text)

@admin_bp.route("/admin/benches")
@login_required
@admin_required
def manage_benches():
    benches = Bench.query.order_by(Bench.id).all()

    return render_template("admin/benches.html", benches=benches)

@admin_bp.route("/admin/benches/update", methods=["POST"])
@login_required
@admin_required
def update_bench():
    data = request.get_json()
    bench = Bench.query.get_or_404(data["bench_id"])

    if "name" in data: 
        bench.name = data["name"]

    if "cell" in data:
        bench.cell = data["cell"]

    if "x" in data:
        bench.x = data["x"]

    if "y" in data:
        bench.y = data["y"]

    if "active" in data:
        bench.active = data["active"]

    if "width" in data:
        bench.width = data["width"]

    if "height" in data:
        bench.height = data["height"]

    if "name" in data:
        bench.name = data["name"]

    if "cell" in data:
        bench.cell = data["cell"]

    db.session.commit()

    write_audit(session["initials"], "UPDATE_BENCH", f"Updated {bench.name}")

    socketio.emit("bench_updated", { "bench_id": bench.id })
    return jsonify(success=True)

@admin_bp.route("/admin/benches/delete", methods=["POST"])
def delete_bench():
    data = request.get_json()
    bench = Bench.query.get(data["bench_id"])

    if not bench:
        return jsonify(success=False)

    db.session.delete(bench)
    db.session.commit()

    socketio.emit("bench_deleted", { "bench_id": bench.id })
    return jsonify(success=True)

@admin_bp.route("/admin/benches/create", methods=["POST"])
def create_bench():
    data = request.get_json()

    highest = db.session.query(db.func.max(db.cast(Bench.name, db.Integer))).scalar() or 0

    bench = Bench(
        name=str(highest + 1),
        cell=data["cell"],
        x=data["x"],
        y=data["y"],
        width=data["width"],
        height=data["height"],
        active=data["active"]
    )

    db.session.add(bench)
    db.session.commit()

    socketio.emit("bench_created", { "bench_id": bench.id })
    return jsonify(success=True, bench_id=bench.id)