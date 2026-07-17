from flask import Flask, render_template
from flask_login import current_user

from config import Config
from app.extensions import db, login_manager, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Blueprints
    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp
    from app.hr.routes import hr_bp
    from app.manager.routes import manager_bp
    from app.employee.routes import employee_bp
    from app.ai.routes import ai_bp
    from app.main.routes import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(hr_bp, url_prefix="/hr")
    app.register_blueprint(manager_bp, url_prefix="/manager")
    app.register_blueprint(employee_bp, url_prefix="/employee")
    app.register_blueprint(ai_bp, url_prefix="/ai")

    @app.context_processor
    def inject_globals():
        return {"app_name": app.config.get("APP_NAME"), "current_user": current_user}

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app
