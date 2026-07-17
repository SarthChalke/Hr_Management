import csv
import io
from datetime import date

from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required

from app.extensions import db
from app.models import User, Employee, Department, Attendance, Leave, ROLE_HR_MANAGER, ROLE_EMPLOYEE
from app.forms import EmployeeForm, LeaveDecisionForm
from app.utils import roles_required

hr_bp = Blueprint("hr", __name__)


@hr_bp.route("/dashboard")
@login_required
@roles_required(ROLE_HR_MANAGER)
def dashboard():
    total_employees = Employee.query.count()
    active_employees = Employee.query.filter_by(status="Active").count()
    pending_final_approval = Leave.query.filter_by(status="Manager Approved").count()
    today_present = Attendance.query.filter_by(date=date.today(), status="Present").count()

    recent_leaves = Leave.query.order_by(Leave.applied_at.desc()).limit(5).all()

    return render_template(
        "hr/dashboard.html",
        total_employees=total_employees,
        active_employees=active_employees,
        pending_final_approval=pending_final_approval,
        today_present=today_present,
        recent_leaves=recent_leaves,
    )


# --- Employee management ----------------------------------------------------

@hr_bp.route("/employees")
@login_required
@roles_required(ROLE_HR_MANAGER)
def employees():
    q = request.args.get("q", "").strip()
    dept_id = request.args.get("department", type=int)

    query = Employee.query.join(User)
    if q:
        query = query.filter(
            User.name.ilike(f"%{q}%")
            | User.email.ilike(f"%{q}%")
            | Employee.employee_code.ilike(f"%{q}%")
        )
    if dept_id:
        query = query.filter(Employee.department_id == dept_id)

    all_employees = query.order_by(Employee.employee_code).all()
    departments = Department.query.order_by(Department.name).all()
    return render_template(
        "hr/employees.html", employees=all_employees, departments=departments, q=q, dept_id=dept_id
    )


@hr_bp.route("/employees/export.csv")
@login_required
@roles_required(ROLE_HR_MANAGER)
def export_employees_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Employee Code", "Name", "Email", "Department", "Designation",
        "Phone", "Salary", "Date of Joining", "Experience (yrs)", "Status",
    ])
    for emp in Employee.query.join(User).order_by(Employee.employee_code).all():
        writer.writerow([
            emp.employee_code, emp.name, emp.email,
            emp.department.name if emp.department else "-",
            emp.designation or "-", emp.phone or "-", emp.salary or 0,
            emp.date_of_joining, emp.experience_years or 0, emp.status,
        ])
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=employees_export.csv"},
    )


@hr_bp.route("/employees/new", methods=["GET", "POST"])
@login_required
@roles_required(ROLE_HR_MANAGER)
def new_employee():
    form = EmployeeForm()
    form.department_id.choices = [(0, "-- None --")] + [
        (d.id, d.name) for d in Department.query.order_by(Department.name).all()
    ]
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.strip().lower()).first():
            flash("A user with that email already exists.", "danger")
        elif Employee.query.filter_by(employee_code=form.employee_code.data.strip()).first():
            flash("That employee code is already in use.", "danger")
        elif not form.password.data:
            flash("Password is required for a new employee login.", "danger")
        else:
            user = User(
                name=form.name.data.strip(),
                email=form.email.data.strip().lower(),
                role=ROLE_EMPLOYEE,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()

            emp = Employee(
                user_id=user.id,
                employee_code=form.employee_code.data.strip(),
                department_id=form.department_id.data or None,
                designation=form.designation.data,
                phone=form.phone.data,
                address=form.address.data,
                salary=form.salary.data or 0,
                date_of_joining=form.date_of_joining.data or date.today(),
                skills=form.skills.data,
                experience_years=form.experience_years.data or 0,
                status=form.status.data,
            )
            db.session.add(emp)
            db.session.commit()
            flash(f"Employee '{user.name}' added.", "success")
            return redirect(url_for("hr.employees"))
    return render_template("hr/employee_form.html", form=form, title="New Employee")


@hr_bp.route("/employees/<int:emp_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required(ROLE_HR_MANAGER)
def edit_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    form = EmployeeForm(obj=emp)
    form.department_id.choices = [(0, "-- None --")] + [
        (d.id, d.name) for d in Department.query.order_by(Department.name).all()
    ]
    if request.method == "GET":
        form.name.data = emp.name
        form.email.data = emp.email
        form.department_id.data = emp.department_id or 0

    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if existing and existing.id != emp.user_id:
            flash("Another user already uses that email.", "danger")
        else:
            emp.user.name = form.name.data.strip()
            emp.user.email = form.email.data.strip().lower()
            if form.password.data:
                emp.user.set_password(form.password.data)

            emp.employee_code = form.employee_code.data.strip()
            emp.department_id = form.department_id.data or None
            emp.designation = form.designation.data
            emp.phone = form.phone.data
            emp.address = form.address.data
            emp.salary = form.salary.data or 0
            emp.date_of_joining = form.date_of_joining.data or emp.date_of_joining
            emp.skills = form.skills.data
            emp.experience_years = form.experience_years.data or 0
            emp.status = form.status.data
            db.session.commit()
            flash("Employee updated.", "success")
            return redirect(url_for("hr.employees"))
    return render_template("hr/employee_form.html", form=form, title="Edit Employee", emp=emp)


@hr_bp.route("/employees/<int:emp_id>/delete", methods=["POST"])
@login_required
@roles_required(ROLE_HR_MANAGER)
def delete_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    user = emp.user
    db.session.delete(emp)
    db.session.delete(user)
    db.session.commit()
    flash("Employee removed.", "info")
    return redirect(url_for("hr.employees"))


# --- Leave final approval ----------------------------------------------------

@hr_bp.route("/leaves")
@login_required
@roles_required(ROLE_HR_MANAGER)
def leaves():
    status_filter = request.args.get("status", "")
    query = Leave.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    all_leaves = query.order_by(Leave.applied_at.desc()).all()
    return render_template("hr/leaves.html", leaves=all_leaves, status_filter=status_filter)


@hr_bp.route("/leaves/<int:leave_id>/decide", methods=["POST"])
@login_required
@roles_required(ROLE_HR_MANAGER)
def decide_leave(leave_id):
    from datetime import datetime

    leave = Leave.query.get_or_404(leave_id)
    form = LeaveDecisionForm()
    if leave.status != "Manager Approved":
        flash("This leave request is not yet awaiting HR approval.", "warning")
        return redirect(url_for("hr.leaves"))

    if form.submit_approve.data:
        leave.status = "Approved"
        leave.hr_remark = form.remark.data
        leave.decided_at = datetime.utcnow()
        flash("Leave approved.", "success")
    elif form.submit_reject.data:
        leave.status = "Rejected"
        leave.hr_remark = form.remark.data
        leave.decided_at = datetime.utcnow()
        flash("Leave rejected.", "info")
    db.session.commit()
    return redirect(url_for("hr.leaves"))


# --- Attendance reports -------------------------------------------------------

@hr_bp.route("/attendance")
@login_required
@roles_required(ROLE_HR_MANAGER)
def attendance_report():
    day = request.args.get("date")
    selected_date = date.fromisoformat(day) if day else date.today()
    records = (
        Attendance.query.join(Employee)
        .filter(Attendance.date == selected_date)
        .all()
    )
    return render_template("hr/attendance_report.html", records=records, selected_date=selected_date)
