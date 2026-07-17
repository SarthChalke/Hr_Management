from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

from app.utils import dashboard_url_for_role

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for(dashboard_url_for_role(current_user.role)))
    return render_template("main/landing.html")
