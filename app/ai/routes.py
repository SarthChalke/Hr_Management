from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user

from app.models import Employee, ROLE_HR_MANAGER, ROLE_DEPT_MANAGER, ROLE_EMPLOYEE, ROLE_SUPER_ADMIN
from app.forms import ChatbotForm
from app.ai_engine import ask_hr_chatbot, analyze_employee_performance

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/chatbot", methods=["GET", "POST"])
@login_required
def chatbot():
    form = ChatbotForm()
    answer = None
    question = None
    if form.validate_on_submit():
        question = form.message.data
        answer = ask_hr_chatbot(question)
    return render_template("ai/chatbot.html", form=form, answer=answer, question=question)


@ai_bp.route("/chatbot/api", methods=["POST"])
@login_required
def chatbot_api():
    """JSON endpoint so the chat widget can be used without a full page reload."""
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    answer = ask_hr_chatbot(message)
    return jsonify({"answer": answer})


@ai_bp.route("/performance/<int:emp_id>")
@login_required
def performance(emp_id):
    emp = Employee.query.get_or_404(emp_id)

    allowed = False
    if current_user.role in (ROLE_SUPER_ADMIN, ROLE_HR_MANAGER):
        allowed = True
    elif current_user.role == ROLE_DEPT_MANAGER and emp.department and emp.department.head_id == current_user.id:
        allowed = True
    elif current_user.role == ROLE_EMPLOYEE and current_user.employee and current_user.employee.id == emp.id:
        allowed = True

    if not allowed:
        abort(403)

    result = analyze_employee_performance(emp)
    return render_template("ai/performance.html", emp=emp, result=result)
