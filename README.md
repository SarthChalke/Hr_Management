# AI HR & Employee Management Portal

A role-based HR & Employee Management web app built with **Flask + PostgreSQL**,
Bootstrap 5, and a fully offline, rule-based "AI" layer (chatbot + performance
analyzer) — no external API key required.

This is a **scoped v1** of a much larger master spec. See [What's included](#whats-included-vs-deferred)
below for exactly what's built vs. what would come in later rounds (Payroll,
Recruitment, and the full diagram/documentation set).

---

## Tech Stack

- **Backend:** Python 3, Flask, Flask-Login, Flask-WTF (CSRF protection)
- **Database:** PostgreSQL via SQLAlchemy + `psycopg[binary]` (v3 driver)
- **Frontend:** Bootstrap 5, Bootstrap Icons, Chart.js, vanilla JS
- **AI layer:** Rule-based, offline (`app/ai_engine.py`) — no OpenAI/Gemini key needed

---

## 1. Prerequisites

- Python 3.10+
- PostgreSQL 13+ running locally (or a connection string to a remote instance)

## 2. Setup (Windows PowerShell)

```powershell
# From the project folder
python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

# Copy the environment template and edit it
copy .env.example .env
notepad .env   # set DATABASE_URL to your PostgreSQL connection string
```

If `psycopg[binary]` fails to install on Windows, make sure you're on Python
3.10–3.12 and have the latest pip: `python -m pip install --upgrade pip`.

### Create the database (PowerShell, using `psql`)

```powershell
psql -U postgres -c "CREATE DATABASE hr_portal;"
psql -U postgres -c "CREATE USER hr_user WITH PASSWORD 'hr_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE hr_portal TO hr_user;"
```

Update `DATABASE_URL` in `.env` to match whatever user/password/db name you used.

### Create tables and demo data

```powershell
python seed.py
```

This creates all tables and seeds:
- 1 Super Admin, 1 HR Manager, 2 Department Managers, 6 Employees
- 2 Departments (Engineering, Human Resources)
- ~15 days of attendance history per employee (today is left open so you can
  do a live check-in during a demo)
- A few sample leave requests in different workflow states

Demo logins are printed at the end of the script, and also shown on the login
page itself.

### Run the app

```powershell
python run.py
```

Visit `http://127.0.0.1:5000`. The app also binds to `0.0.0.0`, so it's
reachable from other devices on your LAN at `http://<your-ip>:5000` (make
sure Windows Firewall allows inbound connections on port 5000).

## 2b. Setup (macOS/Linux)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env with your DATABASE_URL
python seed.py
python run.py
```

---



Five more employees are seeded with the password `Employee@123` (see
`seed.py` for the full list/emails).

---

## What's Included vs. Deferred

The original master prompt describes a very large enterprise HR suite
(Payroll, Recruitment, 8 AI features, full diagram set, 15+ documentation
deliverables). Building all of that in one pass would produce a shallow,
broken shell rather than something you can actually demo — so this v1 is
scoped to a solid, fully working core, per your earlier choice:

### ✅ Built and working
- **Auth:** login, logout, change password, RBAC (4 roles), password hashing
- **User & Department management** (Super Admin)
- **Employee management:** full CRUD, search, department filter, CSV export (HR Manager)
- **Attendance:** live check-in/check-out with late detection, per-employee
  history, HR-wide daily report, manager team report
- **Leave management:** apply → manager approval → HR approval workflow,
  with 4 leave types
- **Dashboards:** role-specific KPI cards + Chart.js charts (dept headcount,
  role distribution)
- **AI (simulated, offline):**
  - HR Chatbot — keyword-matched answers on leave policy, attendance, salary, holidays
  - Performance Analyzer — transparent, explainable scoring from real
    attendance/leave data (not a black box)

### 🔜 Not yet built (natural next round)
- Payroll module (salary slips, deductions, PF/tax, payroll dashboard)
- Recruitment module (job posts, resume upload, AI resume scoring)
- Remaining AI features: resume screening, interview question generator,
  leave prediction, payroll insight detection
- Notifications (email alerts, birthday/anniversary reminders)
- Global search across modules
- OTP/email verification for registration
- Diagrams (ER, DFD, use case, sequence, class, activity) and the full
  documentation set (test cases, project report, user/admin manuals)

If you want, I can build any of these next — Payroll and Recruitment are the
most natural additions to this codebase, and the diagrams/report are best
generated once the module set is final so they accurately reflect the build.

---

## Project Structure

```
hr_portal/
├── app/
│   ├── __init__.py          # App factory, blueprint registration
│   ├── models.py             # SQLAlchemy models
│   ├── forms.py               # WTForms
│   ├── utils.py                # RBAC decorator, helpers
│   ├── ai_engine.py             # Offline rule-based chatbot + performance scoring
│   ├── auth/, admin/, hr/, manager/, employee/, ai/, main/
│   │                            # Blueprints (routes.py in each)
│   ├── templates/               # Jinja2 templates, mirrors blueprint structure
│   └── static/css/js            # Stylesheet + small JS helpers
├── config.py                    # Env-based config, DATABASE_URL normalization
├── run.py                       # Entry point
├── seed.py                      # Creates tables + demo data
├── requirements.txt
└── .env.example
```

## Notes on Deployment

- `config.py` normalizes `postgres://` URLs (as given by some hosts) to the
  `postgresql+psycopg://` form SQLAlchemy 2.x + psycopg3 expect.
- For a LAN demo, `run.py` binds to `0.0.0.0` — allow port 5000 through your
  firewall.
- For anything beyond a local demo, put this behind a real WSGI server
  (gunicorn/waitress) rather than `python run.py`.
