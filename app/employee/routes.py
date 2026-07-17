from datetime import date, datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Attendance, Leave, ROLE_EMPLOYEE
from app.forms import LeaveApplicationForm
from app.utils import roles_required

employee_bp = Blueprint("employee", __name__)


def _current_employee():
    if not current_user.employee:
        abort(404, description="No employee profile linked to this account.")
    return current_user.employee


@employee_bp.route("/dashboard")
@login_required
@roles_required(ROLE_EMPLOYEE)
def dashboard():
    emp = _current_employee()
    recent_attendance = emp.attendances.order_by(Attendance.date.desc()).limit(10).all()
    recent_leaves = emp.leaves.order_by(Leave.applied_at.desc()).limit(5).all()
    today_record = emp.attendances.filter_by(date=date.today()).first()
    return render_template(
        "employee/dashboard.html", emp=emp, recent_attendance=recent_attendance,
        recent_leaves=recent_leaves, today_record=today_record,
    )


@employee_bp.route("/attendance/check-in", methods=["POST"])
@login_required
@roles_required(ROLE_EMPLOYEE)
def check_in():
    emp = _current_employee()
    today = date.today()
    record = emp.attendances.filter_by(date=today).first()
    now = datetime.now().time()
    is_late = now.hour > 9 or (now.hour == 9 and now.minute > 15)

    if record:
        flash("You have already checked in today.", "warning")
    else:
        record = Attendance(
            employee_id=emp.id, date=today, check_in=now,
            status="Late" if is_late else "Present",
        )
        db.session.add(record)
        db.session.commit()
        flash(f"Checked in at {now.strftime('%H:%M')}.", "success")
    return redirect(url_for("employee.dashboard"))


@employee_bp.route("/attendance/check-out", methods=["POST"])
@login_required
@roles_required(ROLE_EMPLOYEE)
def check_out():
    emp = _current_employee()
    today = date.today()
    record = emp.attendances.filter_by(date=today).first()
    if not record or not record.check_in:
        flash("You need to check in first.", "warning")
    elif record.check_out:
        flash("You have already checked out today.", "warning")
    else:
        now = datetime.now()
        record.check_out = now.time()
        check_in_dt = datetime.combine(today, record.check_in)
        record.work_hours = round((now - check_in_dt).total_seconds() / 3600, 2)
        db.session.commit()
        flash(f"Checked out at {now.strftime('%H:%M')}. Worked {record.work_hours} hrs.", "success")
    return redirect(url_for("employee.dashboard"))


@employee_bp.route("/attendance")
@login_required
@roles_required(ROLE_EMPLOYEE)
def attendance_history():
    emp = _current_employee()
    records = emp.attendances.order_by(Attendance.date.desc()).all()
    return render_template("employee/attendance_history.html", records=records, emp=emp)


@employee_bp.route("/leave", methods=["GET", "POST"])
@login_required
@roles_required(ROLE_EMPLOYEE)
def apply_leave():
    emp = _current_employee()
    form = LeaveApplicationForm()
    if form.validate_on_submit():
        if form.end_date.data < form.start_date.data:
            flash("End date cannot be before start date.", "danger")
        else:
            leave = Leave(
                employee_id=emp.id,
                leave_type=form.leave_type.data,
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                reason=form.reason.data,
            )
            db.session.add(leave)
            db.session.commit()
            flash("Leave request submitted. Awaiting manager approval.", "success")
            return redirect(url_for("employee.apply_leave"))

    my_leaves = emp.leaves.order_by(Leave.applied_at.desc()).all()
    return render_template("employee/leave.html", form=form, leaves=my_leaves)


@employee_bp.route("/profile")
@login_required
@roles_required(ROLE_EMPLOYEE)
def profile():
    emp = _current_employee()
    return render_template("employee/profile.html", emp=emp)
