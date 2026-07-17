"""
Lightweight, fully offline "AI" simulation layer.

No external API key is required. The chatbot uses keyword matching against
an HR knowledge base, and the performance analyzer uses a transparent
rule-based scoring formula over attendance and leave data. Both are written
so they can be swapped for a real OpenAI/Gemini call later - just replace
the body of `ask_hr_chatbot()` and `analyze_employee_performance()` with an
API call and keep the same function signature.
"""
from datetime import date, timedelta

from app.models import Attendance, Leave

KNOWLEDGE_BASE = [
    {
        "keywords": ["leave policy", "leave types", "casual leave", "sick leave", "earned leave", "maternity"],
        "answer": (
            "We offer four leave types: Casual Leave (for short personal needs), "
            "Sick Leave (for illness, medical certificate may be required beyond 2 days), "
            "Earned Leave (accrued leave that can be planned in advance), and "
            "Maternity Leave (as per statutory entitlement). Leave requests go through "
            "your Department Manager first, then final HR approval."
        ),
    },
    {
        "keywords": ["apply leave", "how to apply", "request leave"],
        "answer": (
            "Go to Employee Dashboard -> Apply Leave, choose the leave type and dates, "
            "add a reason, and submit. Your manager approves it first, then HR gives "
            "final approval. You can track the status on the same page."
        ),
    },
    {
        "keywords": ["salary", "payroll", "salary slip", "pay slip"],
        "answer": (
            "Salary details are visible on your profile. Salary slips and payroll "
            "processing will appear here once the Payroll module is enabled for your "
            "organization."
        ),
    },
    {
        "keywords": ["attendance", "check in", "check out", "late"],
        "answer": (
            "Attendance is marked daily with a check-in and check-out time. Arriving "
            "after the configured cut-off marks you 'Late'. Your monthly attendance "
            "summary is visible on your dashboard."
        ),
    },
    {
        "keywords": ["holiday", "holidays", "week off"],
        "answer": (
            "Public holidays are set by the organization calendar. Please check with "
            "HR or your department notice board for the current holiday list."
        ),
    },
    {
        "keywords": ["benefits", "perks"],
        "answer": (
            "Standard benefits typically include paid leave, provident fund (PF) "
            "contribution where applicable, and any organization-specific perks "
            "communicated by HR."
        ),
    },
    {
        "keywords": ["performance", "kpi", "review", "evaluation"],
        "answer": (
            "Performance is evaluated using attendance consistency, approved leave "
            "frequency, and manager feedback. You can view your latest performance "
            "score from the AI Performance Analyzer on your dashboard."
        ),
    },
    {
        "keywords": ["hello", "hi", "hey"],
        "answer": "Hello! I'm your HR assistant. Ask me about leave policy, attendance, salary, or holidays.",
    },
]

FALLBACK_ANSWER = (
    "I don't have a specific answer for that yet. Please contact your HR Manager "
    "directly, or try asking about leave policy, attendance, salary, or holidays."
)


def ask_hr_chatbot(user_message: str) -> str:
    """Very small keyword-matching 'AI' chatbot. Deterministic and offline."""
    if not user_message or not user_message.strip():
        return "Please type a question about leave, attendance, salary, or company policy."

    message = user_message.lower()
    best_match = None
    best_score = 0

    for entry in KNOWLEDGE_BASE:
        score = sum(1 for kw in entry["keywords"] if kw in message)
        if score > best_score:
            best_score = score
            best_match = entry

    if best_match and best_score > 0:
        return best_match["answer"]
    return FALLBACK_ANSWER


def analyze_employee_performance(employee) -> dict:
    """
    Rule-based performance scoring using the last 30 days of attendance and leave.
    Returns a dict with score (0-100), label, strengths, weaknesses, suggestions.
    This mirrors what the spec calls the 'AI Employee Performance Analyzer' but is
    implemented as transparent, explainable rules instead of a black-box model.
    """
    today = date.today()
    window_start = today - timedelta(days=30)

    attendance_records = (
        Attendance.query.filter(
            Attendance.employee_id == employee.id, Attendance.date >= window_start
        ).all()
    )

    total_days = len(attendance_records) or 1
    present_days = sum(1 for a in attendance_records if a.status == "Present")
    late_days = sum(1 for a in attendance_records if a.status == "Late")
    absent_days = sum(1 for a in attendance_records if a.status == "Absent")

    attendance_rate = present_days / total_days if total_days else 0

    recent_leaves = (
        Leave.query.filter(
            Leave.employee_id == employee.id, Leave.start_date >= window_start
        ).all()
    )
    approved_leaves = sum(1 for l in recent_leaves if l.status == "Approved")

    # Transparent scoring formula (out of 100)
    score = 100
    score -= absent_days * 6
    score -= late_days * 3
    score -= max(0, approved_leaves - 2) * 4  # more than 2 leaves/month trims score
    score = max(0, min(100, round(score)))

    if score >= 85:
        label = "Excellent"
    elif score >= 70:
        label = "Good"
    elif score >= 50:
        label = "Needs Improvement"
    else:
        label = "At Risk"

    strengths, weaknesses, suggestions = [], [], []

    if attendance_rate >= 0.9:
        strengths.append("Consistently present and reliable.")
    if late_days == 0:
        strengths.append("No late check-ins in the last 30 days.")
    if approved_leaves <= 1:
        strengths.append("Low leave usage, strong availability.")

    if absent_days > 2:
        weaknesses.append(f"{absent_days} unmarked/absent days in the last 30 days.")
        suggestions.append("Discuss recurring absences and any support needed.")
    if late_days > 2:
        weaknesses.append(f"{late_days} late arrivals in the last 30 days.")
        suggestions.append("Review commute/schedule constraints causing lateness.")
    if approved_leaves > 3:
        weaknesses.append(f"{approved_leaves} approved leaves this month, above average.")
        suggestions.append("Check in on workload or wellbeing.")

    if not strengths:
        strengths.append("No standout metrics yet - keep gathering data.")
    if not weaknesses:
        weaknesses.append("No significant concerns detected this period.")
    if not suggestions:
        suggestions.append("Maintain current performance and consistency.")

    return {
        "score": score,
        "label": label,
        "attendance_rate": round(attendance_rate * 100, 1),
        "present_days": present_days,
        "late_days": late_days,
        "absent_days": absent_days,
        "approved_leaves": approved_leaves,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions,
    }
