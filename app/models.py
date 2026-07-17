from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db

# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------
ROLE_SUPER_ADMIN = "super_admin"
ROLE_HR_MANAGER = "hr_manager"
ROLE_DEPT_MANAGER = "dept_manager"
ROLE_EMPLOYEE = "employee"

ALL_ROLES = [ROLE_SUPER_ADMIN, ROLE_HR_MANAGER, ROLE_DEPT_MANAGER, ROLE_EMPLOYEE]

ROLE_LABELS = {
    ROLE_SUPER_ADMIN: "Super Admin",
    ROLE_HR_MANAGER: "HR Manager",
    ROLE_DEPT_MANAGER: "Department Manager",
    ROLE_EMPLOYEE: "Employee",
}

LEAVE_TYPES = ["Casual Leave", "Sick Leave", "Earned Leave", "Maternity Leave"]

LEAVE_STATUS_PENDING = "Pending"
LEAVE_STATUS_MANAGER_APPROVED = "Manager Approved"
LEAVE_STATUS_APPROVED = "Approved"
LEAVE_STATUS_REJECTED = "Rejected"

ATTENDANCE_PRESENT = "Present"
ATTENDANCE_ABSENT = "Absent"
ATTENDANCE_LATE = "Late"
ATTENDANCE_ON_LEAVE = "On Leave"


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_EMPLOYEE)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship(
        "Employee", backref="user", uselist=False, cascade="all, delete-orphan"
    )

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    @property
    def role_label(self) -> str:
        return ROLE_LABELS.get(self.role, self.role)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    budget = db.Column(db.Numeric(12, 2), default=0)
    head_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    head = db.relationship("User", foreign_keys=[head_id])
    employees = db.relationship("Employee", backref="department", lazy="dynamic")

    @property
    def employee_count(self):
        return self.employees.count()

    def __repr__(self):
        return f"<Department {self.name}>"


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    employee_code = db.Column(db.String(20), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)

    designation = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    salary = db.Column(db.Numeric(12, 2), default=0)
    date_of_joining = db.Column(db.Date, default=date.today)
    skills = db.Column(db.String(255))
    experience_years = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default="Active")  # Active / Inactive
    photo = db.Column(db.String(255), nullable=True)

    attendances = db.relationship(
        "Attendance", backref="employee", lazy="dynamic", cascade="all, delete-orphan"
    )
    leaves = db.relationship(
        "Leave", backref="employee", lazy="dynamic", cascade="all, delete-orphan"
    )

    @property
    def name(self):
        return self.user.name if self.user else "-"

    @property
    def email(self):
        return self.user.email if self.user else "-"

    def __repr__(self):
        return f"<Employee {self.employee_code}>"


class Attendance(db.Model):
    __tablename__ = "attendance"
    __table_args__ = (db.UniqueConstraint("employee_id", "date", name="uq_employee_date"),)

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    check_in = db.Column(db.Time, nullable=True)
    check_out = db.Column(db.Time, nullable=True)
    status = db.Column(db.String(20), default=ATTENDANCE_PRESENT)
    work_hours = db.Column(db.Float, default=0)

    def __repr__(self):
        return f"<Attendance emp={self.employee_id} {self.date} {self.status}>"


class Leave(db.Model):
    __tablename__ = "leaves"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    leave_type = db.Column(db.String(30), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(30), default=LEAVE_STATUS_PENDING)
    manager_remark = db.Column(db.String(255))
    hr_remark = db.Column(db.String(255))
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    decided_at = db.Column(db.DateTime, nullable=True)

    @property
    def days(self):
        return (self.end_date - self.start_date).days + 1

    def __repr__(self):
        return f"<Leave emp={self.employee_id} {self.leave_type} {self.status}>"
