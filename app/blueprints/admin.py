"""
app/blueprints/admin.py
Admin blueprint: login, logout, secured admin dashboard with model analytics.
"""

import json
import logging
from datetime import datetime, timezone

from flask import (
    Blueprint, render_template, request, flash,
    redirect, url_for, current_app
)
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models.user import AdminUser
from app.models.prediction import Prediction

logger = logging.getLogger(__name__)
admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    """Admin login page."""
    if current_user.is_authenticated:
        return redirect(url_for("admin.panel"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = AdminUser.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            user.record_login()
            flash(f"Welcome back, {user.username}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("admin.panel"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("auth/admin_login.html")


@admin_bp.route("/logout")
@login_required
def logout():
    """Logout the admin user."""
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@login_required
def panel():
    """Admin dashboard with model metrics, confusion matrix, feature importance."""
    # Load ML metrics
    from app.utils.ml_engine import get_engine
    try:
        engine = get_engine()
        metrics = engine.get_metrics() or {}
        feature_importance = engine.get_feature_importance("random_forest") or {}
    except Exception as exc:
        logger.error(f"Failed to load ML metrics: {exc}")
        metrics = {}
        feature_importance = {}

    # DB stats
    total        = Prediction.query.count()
    approved     = Prediction.query.filter_by(result="Approved").count()
    rejected     = Prediction.query.filter_by(result="Rejected").count()
    today_count  = Prediction.query.filter(
        Prediction.created_at >= datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    ).count()

    recent = (
        Prediction.query
        .order_by(Prediction.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "dashboard/admin.html",
        metrics=metrics,
        feature_importance=feature_importance,
        total=total,
        approved=approved,
        rejected=rejected,
        today_count=today_count,
        recent=recent,
    )


@admin_bp.route("/retrain", methods=["POST"])
@login_required
def retrain():
    """Trigger model retraining."""
    try:
        from app.utils.ml_engine import get_engine
        engine = get_engine()
        metrics = engine.train_and_save()
        flash(f"Models retrained successfully. Best accuracy: "
              f"{max(v['accuracy'] for v in metrics.values()):.1f}%", "success")
    except Exception as exc:
        logger.error(f"Retraining failed: {exc}")
        flash(f"Retraining failed: {exc}", "danger")
    return redirect(url_for("admin.panel"))
