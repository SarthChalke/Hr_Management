"""
Creates all database tables and seeds demo data:
  - 1 Super Admin, 1 HR Manager, 2 Department Managers, 6 Employees
  - 2 Departments (Engineering, Human Resources)
  - ~15 days of attendance history per employee
  - A few sample leave requests in different workflow states

Run with:
    python seed.py
"""
import random
from datetime import date, timedelta, time

from app import create_app
from app.extensions import db
from app.models import (
    User, Employee, Department, Attendance, Leave,
    ROLE_SUPER_ADMIN, ROLE_HR_MANAGER, ROLE_DEPT_MANAGER, ROLE_EMPLOYEE,
)

app = create_app()


def run():
    with app.app_context():
        print("Creating tables...")
        db.create_all()

        if User.query.first():
            print("Database already has data. Skipping seed. "
                  "Drop the tables first if you want to reseed.")
            return

        print("Seeding users...")
        admin = User(name="System Administrator", email="admin@hrportal.com", role=ROLE_SUPER_ADMIN)
        admin.set_password("Admin@123")

        hr = User(name="Priya Sharma", email="hr@hrportal.com", role=ROLE_HR_MANAGER)
        hr.set_password("Hr@12345")

        eng_manager = User(name="Rohan Deshmukh", email="manager@hrportal.com", role=ROLE_DEPT_MANAGER)
        eng_manager.set_password("Manager@123")

        hr_manager_lead = User(name="Anita Kulkarni", email="hrhead@hrportal.com", role=ROLE_DEPT_MANAGER)
        hr_manager_lead.set_password("Manager@123")

        db.session.add_all([admin, hr, eng_manager, hr_manager_lead])
        db.session.flush()

        print("Seeding departments...")
        engineering = Department(
            name="Engineering", description="Product engineering and IT support.",
            budget=1200000, head_id=eng_manager.id,
        )
        hr_dept = Department(
            name="Human Resources", description="Recruitment, payroll, and employee relations.",
            budget=450000, head_id=hr_manager_lead.id,
        )
        db.session.add_all([engineering, hr_dept])
        db.session.flush()

        print("Seeding employee accounts...")
        employee_seed = [
            ("employee@hrportal.com", "Sarthak Patil", "EMP001", engineering, "Software Engineer", "Python, Flask, SQL", 1.5),
            ("neha.joshi@hrportal.com", "Neha Joshi", "EMP002", engineering, "Frontend Developer", "React, CSS, JS", 2.0),
            ("aman.verma@hrportal.com", "Aman Verma", "EMP003", engineering, "QA Engineer", "Testing, Selenium", 1.0),
            ("simran.kaur@hrportal.com", "Simran Kaur", "EMP004", hr_dept, "HR Executive", "Recruitment, Onboarding", 2.5),
            ("vikas.rao@hrportal.com", "Vikas Rao", "EMP005", hr_dept, "Payroll Associate", "Payroll, Excel", 3.0),
            ("isha.mehta@hrportal.com", "Isha Mehta", "EMP006", engineering, "DevOps Engineer", "Docker, CI/CD, Linux", 2.0),
        ]

        employees = []
        for email, name, code, dept, designation, skills, exp in employee_seed:
            u = User(name=name, email=email, role=ROLE_EMPLOYEE)
            u.set_password("Employee@123")
            db.session.add(u)
            db.session.flush()

            emp = Employee(
                user_id=u.id, employee_code=code, department_id=dept.id,
                designation=designation, phone="9876543210",
                address="Pune, Maharashtra", salary=random.randint(28000, 65000),
                date_of_joining=date.today() - timedelta(days=random.randint(120, 900)),
                skills=skills, experience_years=exp, status="Active",
            )
            db.session.add(emp)
            employees.append(emp)

        db.session.flush()

        print("Seeding attendance history (last 15 working days)...")
        today = date.today()
        day_cursor = today - timedelta(days=1)  # start from yesterday so "today" stays open for a live demo check-in
        working_days = []
        while len(working_days) < 15:
            if day_cursor.weekday() < 6:  # skip Sunday
                working_days.append(day_cursor)
            day_cursor -= timedelta(days=1)

        for emp in employees:
            for d in working_days:
                roll = random.random()
                if roll < 0.08:
                    status, check_in, check_out, hours = "Absent", None, None, 0
                elif roll < 0.20:
                    status = "Late"
                    check_in, check_out, hours = time(9, 45), time(18, 10), 8.4
                else:
                    status = "Present"
                    check_in, check_out, hours = time(9, 5), time(18, 5), 9.0

                db.session.add(Attendance(
                    employee_id=emp.id, date=d, check_in=check_in,
                    check_out=check_out, status=status, work_hours=hours,
                ))

        print("Seeding sample leave requests...")
        db.session.add(Leave(
            employee_id=employees[0].id, leave_type="Casual Leave",
            start_date=today + timedelta(days=3), end_date=today + timedelta(days=3),
            reason="Personal work.", status="Pending",
        ))
        db.session.add(Leave(
            employee_id=employees[1].id, leave_type="Sick Leave",
            start_date=today - timedelta(days=5), end_date=today - timedelta(days=4),
            reason="Fever.", status="Manager Approved",
            manager_remark="Approved, get well soon.",
        ))
        db.session.add(Leave(
            employee_id=employees[3].id, leave_type="Earned Leave",
            start_date=today - timedelta(days=20), end_date=today - timedelta(days=18),
            reason="Family function.", status="Approved",
            manager_remark="Approved.", hr_remark="Confirmed.",
        ))
        db.session.add(Leave(
            employee_id=employees[2].id, leave_type="Casual Leave",
            start_date=today - timedelta(days=10), end_date=today - timedelta(days=10),
            reason="Not enough notice given.", status="Rejected",
            manager_remark="Insufficient notice period.",
        ))

        db.session.commit()
        print("\nSeed complete. Demo logins (password shown next to each):")
        print("  Super Admin      admin@hrportal.com        Admin@123")
        print("  HR Manager       hr@hrportal.com           Hr@12345")
        print("  Dept Manager     manager@hrportal.com      Manager@123  (heads Engineering)")
        print("  Dept Manager     hrhead@hrportal.com       Manager@123  (heads Human Resources)")
        print("  Employee         employee@hrportal.com     Employee@123")
        print("  ...and 5 more employees, all with password Employee@123")


if __name__ == "__main__":
    run()
