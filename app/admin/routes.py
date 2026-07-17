from datetime import date, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (
    User, Department, Employee, Attendance, Leave,
    ROLE_SUPER_ADMIN, ROLE_HR_MANAGER, ROLE_DEPT_MANAGER, ROLE_EMPLOYEE,
)
from app.forms import UserForm, DepartmentForm
from app.utils import roles_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/dashboard")
@login_required
@roles_required(ROLE_SUPER_ADMIN)
def dashboard():
    total_employees = Employee.query.count()
    active_employees = Employee.query.filter_by(status="Active").count()
    total_departments = Department.query.count()
    pending_leaves = Leave.query.filter(Leave.status.in_(["Pending", "Manager Approved"])).count()

    today = date.today()
    today_attendance = Attendance.query.filter_by(date=today).count()
    present_today = Attendance.query.filter_by(date=today, status="Present").count()
    attendance_rate = round((present_today / today_attendance) * 100, 1) if today_attendance else 0

    dept_data = [
        {"name": d.name, "count": d.employee_count} for d in Department.query.all()
    ]

    role_counts = {
        "Super Admin": User.query.filter_by(role=ROLE_SUPER_ADMIN).count(),
        "HR Manager": User.query.filter_by(role=ROLE_HR_MANAGER).count(),
        "Dept Manager": User.query.filter_by(role=ROLE_DEPT_MANAGER).count(),
        "Employee": User.query.filter_by(role=ROLE_EMPLOYEE).count(),
    }

    return render_template(
        "admin/dashboard.html",
        total_employees=total_employees,
        active_employees=active_employees,
        total_departments=total_departments,
        pending_leaves=pending_leaves,
        attendance_rate=attendance_rate,
        dept_data=dept_data,
        role_counts=role_counts,
    )


# --- User management -------------------------------------------------------

@admin_bp.route("/users")
@login_required
@roles_required(ROLE_SUPER_ADMIN)
def users():
    q = request.args.get("q", "").strip()
    query = User.query
    if q:
        query = query.filter(User.name.ilike(f"%{q}%") | User.email.ilike(f"%{q}%"))
    all_users = query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users, q=q)


@admin_bp.route("/users/new", methods=["GET", "POST"])
@login_required
@roles_required(ROLE_SUPER_ADMIN)
def new_user():
    form = UserForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.strip().lower()).first():
            flash("A user with that email already exists.", "danger")
        elif not form.password.data:
            flash("Password is required for a new user.", "danger")
        else:
            user = User(
                name=form.name.data.strip(),
                email=form.email.data.strip().lower(),
                role=form.role.data,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash(f"User '{user.name}' created.", "success")
            return redirect(url_for("admin.users"))
    return render_template("admin/user_form.html", form=form, title="New User")


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required(ROLE_SUPER_ADMIN)
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if existing and existing.id != user.id:
            flash("Another user already uses that email.", "danger")
        else:
            user.name = form.name.data.strip()
            user.email = form.email.data.strip().lower()
            user.role = form.role.data
            if form.password.data:
                user.set_password(form.password.data)
            db.session.commit()
            flash("User updated.", "success")
            return redirect(url_for("admin.users"))
    return render_template("admin/user_form.html", form=form, title="Edit User", user=user)


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@roles_required(ROLE_SUPER_ADMIN)
def toggle_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "warning")
    else:
        user.is_active = not user.is_active
        db.session.commit()
        flash(f"User {'activated' if user.is_active else 'deactivated'}.", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@roles_required(ROLE_SUPER_ADMIN)
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "warning")
        return redirect(url_for("admin.users"))
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "info")
    return redirect(url_for("admin.users"))


# --- Department management --------------------------------------------------

@admin_bp.route("/departments")
@login_required
@roles_required(ROLE_SUPER_ADMIN)
def departments():
    all_departments = Department.query.order_by(Department.name).all()
    return render_template("admin/departments.html", departments=all_departments)


@admin_bp.route("/departments/new", methods=["GET", "POST"])
@login_required
@roles_required(ROLE_SUPER_ADMIN)
def new_department():
    form = DepartmentForm()
    form.head_id.choices = [(0, "-- None --")] + [
        (u.id, u.name) for u in User.query.filter(User.role.in_([ROLE_HR_MANAGER, ROLE_DEPT_MANAGER])).all()
    ]
    if form.validate_on_submit():
        dept = Department(
            name=form.name.data.strip(),
            description=form.description.data,
            budget=form.budget.data or 0,
            head_id=form.head_id.data or None,
        )
        db.session.add(dept)
        db.session.commit()
        flash(f"Department '{dept.name}' created.", "success")
        return redirect(url_for("admin.departments"))
    return render_template("admin/department_form.html", form=form, title="New Department")


@admin_bp.route("/departments/<int:dept_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required(ROLE_SUPER_ADMIN)
def edit_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    form = DepartmentForm(obj=dept)
    form.head_id.choices = [(0, "-- None --")] + [
        (u.id, u.name) for u in User.query.filter(User.role.in_([ROLE_HR_MANAGER, ROLE_DEPT_MANAGER])).all()
    ]
    if request.method == "GET":
        form.head_id.data = dept.head_id or 0
    if form.validate_on_submit():
        dept.name = form.name.data.strip()
        dept.description = form.description.data
        dept.budget = form.budget.data or 0
        dept.head_id = form.head_id.data or None
        db.session.commit()
        flash("Department updated.", "success")
        return redirect(url_for("admin.departments"))
    return render_template("admin/department_form.html", form=form, title="Edit Department", dept=dept)


@admin_bp.route("/departments/<int:dept_id>/delete", methods=["POST"])
@login_required
@roles_required(ROLE_SUPER_ADMIN)
def delete_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    if dept.employee_count > 0:
        flash("Cannot delete a department that still has employees assigned.", "danger")
    else:
        db.session.delete(dept)
        db.session.commit()
        flash("Department deleted.", "info")
    return redirect(url_for("admin.departments"))
