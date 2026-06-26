"""
config.py
Flask configuration classes for development, testing, and production.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration shared across environments."""

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # ── Database ──────────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'credit_approval.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # ── Session ───────────────────────────────────────────────────────────────
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # ── IBM Watson ML ─────────────────────────────────────────────────────────
    WATSON_API_KEY = os.environ.get("WATSON_API_KEY", "")
    WATSON_URL = os.environ.get("WATSON_URL", "https://us-south.ml.cloud.ibm.com")
    WATSON_DEPLOYMENT_ID = os.environ.get("WATSON_DEPLOYMENT_ID", "")
    WATSON_SPACE_ID = os.environ.get("WATSON_SPACE_ID", "")
    WATSON_MODEL_ID = os.environ.get("WATSON_MODEL_ID", "")

    # ── Mail ──────────────────────────────────────────────────────────────────
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@creditpredict.ai")

    # ── Pagination ────────────────────────────────────────────────────────────
    PREDICTIONS_PER_PAGE = 10
    HISTORY_PER_PAGE = 15

    # ── ML Models ────────────────────────────────────────────────────────────
    ML_MODELS_DIR = os.path.join(BASE_DIR, "ml_models")
    PRIMARY_MODEL = "xgboost"       # Model used for predictions
    USE_WATSON = False              # Set True to use IBM Watson ML

    # ── Admin ─────────────────────────────────────────────────────────────────
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

    # ── Upload ────────────────────────────────────────────────────────────────
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "instance", "uploads")

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URL = "memory://"

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL = "INFO"
    LOG_FILE = os.path.join(BASE_DIR, "instance", "app.log")

    # ── App Info ──────────────────────────────────────────────────────────────
    APP_NAME = "Credit Card Approval Prediction"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "Predict customer eligibility using Machine Learning and IBM Watson Cloud."


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = True
    LOG_LEVEL = "DEBUG"
    USE_WATSON = os.environ.get("USE_WATSON", "false").lower() == "true"


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    USE_WATSON = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_ENABLED = True
    USE_WATSON = True
    LOG_LEVEL = "WARNING"


# ── Config map ────────────────────────────────────────────────────────────────
config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(env: str = None) -> Config:
    """Return the appropriate configuration class."""
    env = env or os.environ.get("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)
