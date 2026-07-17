from datetime import date, datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Employee, Department, Attendance, Leave, ROLE_DEPT_MANAGER
from app.forms import LeaveDecisionForm
from app.utils import roles_required

manager_bp = Blueprint("manager", __name__)


def _managed_department():
    """The department(s) this manager heads. Simplified: first department where head_id == current_user.id."""
    return Department.query.filter_by(head_id=current_user.id).first()


@manager_bp.route("/dashboard")
@login_required
@roles_required(ROLE_DEPT_MANAGER)
def dashboard():
    dept = _managed_department()
    team_count = dept.employee_count if dept else 0
    pending_leaves = 0
    today_present = 0
    if dept:
        emp_ids = [e.id for e in dept.employees]
        pending_leaves = Leave.query.filter(
            Leave.employee_id.in_(emp_ids), Leave.status == "Pending"
        ).count() if emp_ids else 0
        today_present = Attendance.query.filter(
            Attendance.employee_id.in_(emp_ids), Attendance.date == date.today(), Attendance.status == "Present"
        ).count() if emp_ids else 0

    return render_template(
        "manager/dashboard.html", dept=dept, team_count=team_count,
        pending_leaves=pending_leaves, today_present=today_present,
    )


@manager_bp.route("/team-attendance")
@login_required
@roles_required(ROLE_DEPT_MANAGER)
def team_attendance():
    dept = _managed_department()
    day = request.args.get("date")
    selected_date = date.fromisoformat(day) if day else date.today()

    records = []
    if dept:
        emp_ids = [e.id for e in dept.employees]
        records = Attendance.query.filter(
            Attendance.employee_id.in_(emp_ids), Attendance.date == selected_date
        ).all() if emp_ids else []

    return render_template(
        "manager/team_attendance.html", dept=dept, records=records, selected_date=selected_date
    )


@manager_bp.route("/leaves")
@login_required
@roles_required(ROLE_DEPT_MANAGER)
def leaves():
    dept = _managed_department()
    all_leaves = []
    if dept:
        emp_ids = [e.id for e in dept.employees]
        all_leaves = Leave.query.filter(Leave.employee_id.in_(emp_ids)).order_by(
            Leave.applied_at.desc()
        ).all() if emp_ids else []
    return render_template("manager/leaves.html", leaves=all_leaves, dept=dept)


@manager_bp.route("/leaves/<int:leave_id>/decide", methods=["POST"])
@login_required
@roles_required(ROLE_DEPT_MANAGER)
def decide_leave(leave_id):
    leave = Leave.query.get_or_404(leave_id)
    dept = _managed_department()
    if not dept or leave.employee.department_id != dept.id:
        flash("You can only act on leave requests from your own team.", "danger")
        return redirect(url_for("manager.leaves"))

    if leave.status != "Pending":
        flash("This request has already moved past the manager stage.", "warning")
        return redirect(url_for("manager.leaves"))

    form = LeaveDecisionForm()
    if form.submit_approve.data:
        leave.status = "Manager Approved"
        leave.manager_remark = form.remark.data
        flash("Leave forwarded to HR for final approval.", "success")
    elif form.submit_reject.data:
        leave.status = "Rejected"
        leave.manager_remark = form.remark.data
        leave.decided_at = datetime.utcnow()
        flash("Leave rejected.", "info")
    db.session.commit()
    return redirect(url_for("manager.leaves"))
