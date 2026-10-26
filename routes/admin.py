from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session
)

from werkzeug.security import generate_password_hash

from database.db import db
from database.models import User

from routes.auth import valid_session_required, admin_required

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/users")
@valid_session_required
@admin_required
def manage_users():
    users = User.query.order_by(User.initials).all()

    return render_template("admin/users.html", users=users)

@admin_bp.route("/admin/users/create", methods=["POST"])
@valid_session_required
@admin_required
def create_user():
    initials = request.form["initials"].upper()
    name = request.form["name"]
    password = request.form["password"]

    existing = User.query.filter_by(initials=initials).first()

    if existing:
        return "User already exists", 400

    user = User(initials=initials, name=name, password_hash=generate_password_hash(password), is_admin=False)

    db.session.add(user)
    db.session.commit()

    return redirect("/admin/users")

@admin_bp.route("/admin/users/reset-password/<int:user_id>", methods=["POST"])
@valid_session_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    password = request.form["password"]

    user.password_hash = (generate_password_hash(password))

    db.session.commit()

    return redirect("/admin/users")

@admin_bp.route("/admin/users/toggle-admin/<int:user_id>")
@valid_session_required
@admin_required
def toggle_admin(user_id):
    if user_id == session["user_id"]:
        return "You cannot remove your own admin rights.", 400
    
    user = User.query.get_or_404(user_id)

    user.is_admin = not user.is_admin

    db.session.commit()

    return redirect("/admin/users")

@admin_bp.route("/admin/users/delete/<int:user_id>")
@valid_session_required
@admin_required
def delete_user(user_id):
    if user_id == session["user_id"]:
        return "You cannot delete your own account.", 400

    user = User.query.get_or_404(user_id)

    db.session.delete(user)

    db.session.commit()

    return redirect("/admin/users")

