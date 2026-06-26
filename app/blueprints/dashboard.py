"""
app/blueprints/dashboard.py
Analytics dashboard blueprint with KPI aggregations and chart data.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from flask import Blueprint, render_template, jsonify, request
from sqlalchemy import func, extract

from app import db
from app.models.prediction import Prediction

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def analytics():
    """Main analytics dashboard page."""
    stats = _get_stats()
    chart_data = _get_chart_data()
    recent = (
        Prediction.query
        .order_by(Prediction.created_at.desc())
        .limit(10)
        .all()
    )
    return render_template(
        "dashboard/analytics.html",
        stats=stats,
        chart_data=chart_data,
        recent_predictions=recent,
    )


@dashboard_bp.route("/api/stats")
def api_stats():
    """JSON endpoint for live stat updates."""
    return jsonify(_get_stats())


@dashboard_bp.route("/api/charts")
def api_charts():
    """JSON endpoint for chart data refresh."""
    return jsonify(_get_chart_data())


# ── Private helpers ────────────────────────────────────────────────────────────

def _get_stats() -> dict:
    """Aggregate KPI statistics for the dashboard."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start  = today_start - timedelta(days=7)
    month_start = today_start.replace(day=1)

    total    = Prediction.query.count()
    approved = Prediction.query.filter_by(result="Approved").count()
    rejected = Prediction.query.filter_by(result="Rejected").count()
    today    = Prediction.query.filter(Prediction.created_at >= today_start).count()
    weekly   = Prediction.query.filter(Prediction.created_at >= week_start).count()
    monthly  = Prediction.query.filter(Prediction.created_at >= month_start).count()

    avg_income = db.session.query(func.avg(Prediction.annual_income)).scalar() or 0
    avg_credit = db.session.query(func.avg(Prediction.credit_score)).scalar()  or 0
    avg_loan   = db.session.query(func.avg(Prediction.loan_amount)).scalar()   or 0
    avg_prob   = db.session.query(func.avg(Prediction.probability)).scalar()   or 0

    approval_rate = round(approved / total * 100, 1) if total else 0
    rejection_rate = round(rejected / total * 100, 1) if total else 0

    return {
        "total":          total,
        "approved":       approved,
        "rejected":       rejected,
        "today":          today,
        "weekly":         weekly,
        "monthly":        monthly,
        "approval_rate":  approval_rate,
        "rejection_rate": rejection_rate,
        "avg_income":     round(avg_income, 0),
        "avg_credit":     round(avg_credit, 1),
        "avg_loan":       round(avg_loan, 0),
        "avg_probability": round(avg_prob * 100, 1),
    }


def _get_chart_data() -> dict:
    """Build all chart datasets for the dashboard."""
    # 1. Daily predictions for the last 30 days
    daily = _daily_trend(days=30)

    # 2. Approval by gender
    gender_stats = (
        db.session.query(Prediction.gender, Prediction.result, func.count())
        .group_by(Prediction.gender, Prediction.result)
        .all()
    )
    gender_chart = defaultdict(lambda: {"Approved": 0, "Rejected": 0})
    for g, r, c in gender_stats:
        if g:
            gender_chart[g][r] = c

    # 3. Credit score distribution (buckets)
    buckets = {"300-499": 0, "500-599": 0, "600-649": 0, "650-699": 0, "700-749": 0, "750-850": 0}
    scores = db.session.query(Prediction.credit_score).filter(Prediction.credit_score.isnot(None)).all()
    for (s,) in scores:
        if s < 500:    buckets["300-499"] += 1
        elif s < 600:  buckets["500-599"] += 1
        elif s < 650:  buckets["600-649"] += 1
        elif s < 700:  buckets["650-699"] += 1
        elif s < 750:  buckets["700-749"] += 1
        else:          buckets["750-850"] += 1

    # 4. Employment status breakdown
    emp_stats = (
        db.session.query(Prediction.employment_status, func.count())
        .group_by(Prediction.employment_status)
        .all()
    )

    # 5. Approval by education
    edu_stats = (
        db.session.query(Prediction.education, Prediction.result, func.count())
        .group_by(Prediction.education, Prediction.result)
        .all()
    )
    edu_chart = defaultdict(lambda: {"Approved": 0, "Rejected": 0})
    for e, r, c in edu_stats:
        if e:
            edu_chart[e][r] = c

    # 6. Loan purpose distribution
    purpose_stats = (
        db.session.query(Prediction.loan_purpose, func.count())
        .group_by(Prediction.loan_purpose)
        .all()
    )

    return {
        "daily_trend":  daily,
        "gender":       dict(gender_chart),
        "credit_score_buckets": buckets,
        "employment":   {e: c for e, c in emp_stats if e},
        "education":    dict(edu_chart),
        "loan_purpose": {p: c for p, c in purpose_stats if p},
    }


def _daily_trend(days: int = 30) -> dict:
    """Return daily approved/rejected counts for the last N days."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)

    rows = (
        db.session.query(
            func.date(Prediction.created_at).label("day"),
            Prediction.result,
            func.count().label("cnt"),
        )
        .filter(Prediction.created_at >= start)
        .group_by("day", Prediction.result)
        .order_by("day")
        .all()
    )

    labels = []
    approved_vals = []
    rejected_vals = []
    day_map: dict = defaultdict(lambda: {"Approved": 0, "Rejected": 0})
    for day, result, cnt in rows:
        day_map[str(day)][result] = cnt

    # Fill all days even if no data
    for i in range(days):
        d = (start + timedelta(days=i + 1)).date()
        key = str(d)
        labels.append(d.strftime("%d %b"))
        approved_vals.append(day_map[key]["Approved"])
        rejected_vals.append(day_map[key]["Rejected"])

    return {
        "labels":   labels,
        "approved": approved_vals,
        "rejected": rejected_vals,
    }
