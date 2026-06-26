"""
app/blueprints/main.py
Main blueprint: Home, About, Contact pages.
"""

import logging
from datetime import date, datetime, timezone, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models.prediction import Prediction
from app import db

logger = logging.getLogger(__name__)
main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Homepage with stats and hero section."""
    # Aggregate statistics for the hero cards
    total = Prediction.query.count()
    approved = Prediction.query.filter_by(result="Approved").count()
    rejected = Prediction.query.filter_by(result="Rejected").count()
    today_count = Prediction.query.filter(
        Prediction.created_at >= datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    ).count()

    # Model accuracy pulled from saved metrics if available
    from app.utils.ml_engine import get_engine
    try:
        engine = get_engine()
        metrics = engine.get_metrics() or {}
        best_accuracy = max(
            (v.get("accuracy", 0) for v in metrics.values()),
            default=89.1
        )
    except Exception:
        best_accuracy = 89.1

    return render_template(
        "index.html",
        total_predictions=total,
        approved_count=approved,
        rejected_count=rejected,
        today_count=today_count,
        model_accuracy=round(best_accuracy, 1),
    )


@main_bp.route("/about")
def about():
    """About page — project overview, architecture, technology stack."""
    return render_template("about.html")


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    """Contact page with a simple message form."""
    if request.method == "POST":
        name    = request.form.get("name", "").strip()
        email   = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not all([name, email, message]):
            flash("Please fill in all required fields.", "danger")
        else:
            # In production this would send an email via Flask-Mail
            logger.info(f"Contact form submitted by {name} <{email}>: {subject}")
            flash("Message received! We will get back to you shortly.", "success")
            return redirect(url_for("main.contact"))

    return render_template("contact.html")
