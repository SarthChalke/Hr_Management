from functools import wraps
from flask import abort
from flask_login import current_user


def roles_required(*roles):
    """Restrict a view to one or more roles. Usage: @roles_required('super_admin', 'hr_manager')"""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator


def dashboard_url_for_role(role: str) -> str:
    mapping = {
        "super_admin": "admin.dashboard",
        "hr_manager": "hr.dashboard",
        "dept_manager": "manager.dashboard",
        "employee": "employee.dashboard",
    }
    return mapping.get(role, "employee.dashboard")
