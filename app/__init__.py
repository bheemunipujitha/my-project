"""
app/__init__.py
Flask Application Factory.
Creates and configures the Flask app instance with all extensions,
blueprints, error handlers, and context processors.
"""

import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import get_config

# ── Extension instances (uninitialised) ───────────────────────────────────────
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)


def create_app(env: str = "development") -> Flask:
    """
    Application factory.

    Args:
        env: Configuration environment ('development', 'testing', 'production')

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__, instance_relative_config=True)

    # ── Load configuration ─────────────────────────────────────────────────
    config = get_config(env)
    app.config.from_object(config)

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config.get("UPLOAD_FOLDER", "instance/uploads"), exist_ok=True)

    # ── Initialise extensions ──────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    # ── Login manager config ───────────────────────────────────────────────
    login_manager.login_view = "admin.login"
    login_manager.login_message = "Please log in to access the admin panel."
    login_manager.login_message_category = "warning"

    # ── User loader ────────────────────────────────────────────────────────
    from app.models.user import AdminUser

    @login_manager.user_loader
    def load_user(user_id):
        return AdminUser.query.get(int(user_id))

    # ── Register blueprints ────────────────────────────────────────────────
    _register_blueprints(app)

    # ── Register error handlers ────────────────────────────────────────────
    _register_error_handlers(app)

    # ── Register context processors ────────────────────────────────────────
    _register_context_processors(app)

    # ── Create DB tables ───────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed_admin(app)

    # ── Logging setup ──────────────────────────────────────────────────────
    _configure_logging(app)

    app.logger.info(f"Application '{app.config['APP_NAME']}' started in {env} mode.")
    return app


# ── Private helpers ────────────────────────────────────────────────────────────

def _register_blueprints(app: Flask) -> None:
    """Register all application blueprints."""
    from app.blueprints.main import main_bp
    from app.blueprints.predict import predict_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.history import history_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.ml_info import ml_info_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(predict_bp, url_prefix="/predict")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(history_bp, url_prefix="/history")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(ml_info_bp, url_prefix="/ml")
    app.register_blueprint(api_bp, url_prefix="/api/v1")


def _register_error_handlers(app: Flask) -> None:
    """Register custom error pages."""

    @app.errorhandler(400)
    def bad_request(e):
        return render_template("errors/400.html", error=e), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html", error=e), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html", error=e), 404

    @app.errorhandler(429)
    def too_many_requests(e):
        return render_template("errors/429.html", error=e), 429

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template("errors/500.html", error=e), 500


def _register_context_processors(app: Flask) -> None:
    """Inject global template variables."""

    @app.context_processor
    def inject_globals():
        from app.models.prediction import Prediction
        try:
            total_predictions = Prediction.query.count()
            approved = Prediction.query.filter_by(result="Approved").count()
            rejected = Prediction.query.filter_by(result="Rejected").count()
            approval_rate = round((approved / total_predictions * 100), 1) if total_predictions else 0
        except Exception:
            total_predictions = approved = rejected = 0
            approval_rate = 0.0

        return dict(
            app_name=app.config.get("APP_NAME", "CreditPredict AI"),
            app_version=app.config.get("APP_VERSION", "1.0.0"),
            total_predictions=total_predictions,
            approved_count=approved,
            rejected_count=rejected,
            approval_rate=approval_rate,
        )


def _seed_admin(app: Flask) -> None:
    """Create the default admin user if it doesn't already exist."""
    from app.models.user import AdminUser
    if not AdminUser.query.first():
        admin = AdminUser(
            username=app.config.get("ADMIN_USERNAME", "admin"),
            email="admin@creditpredict.ai",
        )
        admin.set_password(app.config.get("ADMIN_PASSWORD", "admin123"))
        db.session.add(admin)
        db.session.commit()
        app.logger.info("Default admin user created.")


def _configure_logging(app: Flask) -> None:
    """Set up rotating file handler for production logging."""
    if not app.debug:
        log_file = app.config.get("LOG_FILE", "instance/app.log")
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        handler = RotatingFileHandler(log_file, maxBytes=1_048_576, backupCount=10)
        handler.setLevel(logging.WARNING)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(module)s: %(message)s"
        )
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
