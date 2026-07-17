from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SelectField, DecimalField, FloatField,
    DateField, TextAreaField, SubmitField,
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange

from app.models import ALL_ROLES, ROLE_LABELS, LEAVE_TYPES


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(check_deliverability=False)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField(
        "New Password", validators=[DataRequired(), Length(min=6)]
    )
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match")],
    )
    submit = SubmitField("Change Password")


class UserForm(FlaskForm):
    """Used by Super Admin to create/edit users (and implicitly employees)."""
    name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(check_deliverability=False), Length(max=120)])
    password = PasswordField(
        "Password", validators=[Optional(), Length(min=6)],
        description="Leave blank to keep the current password when editing.",
    )
    role = SelectField("Role", choices=[(r, ROLE_LABELS[r]) for r in ALL_ROLES], validators=[DataRequired()])
    submit = SubmitField("Save User")


class DepartmentForm(FlaskForm):
    name = StringField("Department Name", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField("Description", validators=[Optional()])
    budget = DecimalField("Budget", validators=[Optional(), NumberRange(min=0)], places=2)
    head_id = SelectField("Department Head", coerce=int, validators=[Optional()])
    submit = SubmitField("Save Department")


class EmployeeForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(check_deliverability=False), Length(max=120)])
    password = PasswordField(
        "Password", validators=[Optional(), Length(min=6)],
        description="Leave blank to keep the current password when editing.",
    )
    employee_code = StringField("Employee Code", validators=[DataRequired(), Length(max=20)])
    department_id = SelectField("Department", coerce=int, validators=[Optional()])
    designation = StringField("Designation", validators=[Optional(), Length(max=120)])
    phone = StringField("Phone", validators=[Optional(), Length(max=20)])
    address = StringField("Address", validators=[Optional(), Length(max=255)])
    salary = DecimalField("Salary", validators=[Optional(), NumberRange(min=0)], places=2)
    date_of_joining = DateField("Date of Joining", validators=[Optional()])
    skills = StringField("Skills (comma separated)", validators=[Optional(), Length(max=255)])
    experience_years = FloatField("Experience (years)", validators=[Optional(), NumberRange(min=0)])
    status = SelectField("Status", choices=[("Active", "Active"), ("Inactive", "Inactive")])
    submit = SubmitField("Save Employee")


class AttendanceForm(FlaskForm):
    date = DateField("Date", validators=[DataRequired()])
    check_in = StringField("Check-in (HH:MM)", validators=[Optional()])
    check_out = StringField("Check-out (HH:MM)", validators=[Optional()])
    status = SelectField(
        "Status",
        choices=[("Present", "Present"), ("Absent", "Absent"), ("Late", "Late"), ("On Leave", "On Leave")],
    )
    submit = SubmitField("Save Attendance")


class LeaveApplicationForm(FlaskForm):
    leave_type = SelectField("Leave Type", choices=[(t, t) for t in LEAVE_TYPES], validators=[DataRequired()])
    start_date = DateField("Start Date", validators=[DataRequired()])
    end_date = DateField("End Date", validators=[DataRequired()])
    reason = TextAreaField("Reason", validators=[DataRequired(), Length(max=500)])
    submit = SubmitField("Apply for Leave")


class LeaveDecisionForm(FlaskForm):
    remark = StringField("Remark", validators=[Optional(), Length(max=255)])
    submit_approve = SubmitField("Approve")
    submit_reject = SubmitField("Reject")


class ChatbotForm(FlaskForm):
    message = StringField("Ask the HR assistant...", validators=[DataRequired(), Length(max=500)])
    submit = SubmitField("Ask")
