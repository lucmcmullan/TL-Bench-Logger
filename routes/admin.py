from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session
)

from werkzeug.security import generate_password_hash

from scripts.db import db
from scripts.models import AuditLog, User

from datetime import datetime
from utils.audit import write_audit

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
        return "User already exists", 400

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

    write_audit(session["initials"], "RESET_PASSWORD", f"Password reset for user: {user.initials}")

    return redirect("/admin/users")

@admin_bp.route("/admin/users/toggle-admin/<int:user_id>")
@login_required
@admin_required
def toggle_admin(user_id):
    if user_id == session["user_id"]:
        return "You cannot remove your own admin rights.", 400
    
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()

    write_audit(session["initials"], "TOGGLE_ADMIN", f"Admin rights toggled for user: {user.initials}")

    return redirect("/admin/users")

@admin_bp.route("/admin/users/toggle-enabled/<int:user_id>")
@login_required
@admin_required
def toggle_enabled(user_id):
    user = db.session.get(User, user_id)

    if user.id == session["user_id"]:
        return ("You cannot disable yourself.", 400)

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