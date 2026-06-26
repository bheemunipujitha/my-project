"""
app/blueprints/history.py
Prediction history blueprint: paginated table, search, filter, export, delete.
"""

import io
import csv
import json
import logging
from datetime import datetime

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, Response, jsonify, current_app
)
from sqlalchemy import or_

from app import db
from app.models.prediction import Prediction

logger = logging.getLogger(__name__)
history_bp = Blueprint("history", __name__)


@history_bp.route("/")
def index():
    """Paginated prediction history with search and filter."""
    page    = request.args.get("page", 1, type=int)
    search  = request.args.get("search", "").strip()
    result_filter = request.args.get("result", "")
    per_page = current_app.config.get("HISTORY_PER_PAGE", 15)

    query = Prediction.query

    # ── Search ─────────────────────────────────────────────────────────────
    if search:
        query = query.filter(
            or_(
                Prediction.applicant_name.ilike(f"%{search}%"),
                Prediction.applicant_email.ilike(f"%{search}%"),
                Prediction.occupation.ilike(f"%{search}%"),
            )
        )

    # ── Result filter ──────────────────────────────────────────────────────
    if result_filter in ("Approved", "Rejected"):
        query = query.filter_by(result=result_filter)

    pagination = query.order_by(Prediction.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        "dashboard/history.html",
        predictions=pagination.items,
        pagination=pagination,
        search=search,
        result_filter=result_filter,
    )


@history_bp.route("/delete/<int:pred_id>", methods=["POST"])
def delete(pred_id: int):
    """Delete a single prediction record."""
    prediction = Prediction.query.get_or_404(pred_id)
    db.session.delete(prediction)
    db.session.commit()
    flash(f"Prediction #{pred_id} deleted.", "info")
    return redirect(url_for("history.index"))


@history_bp.route("/delete-all", methods=["POST"])
def delete_all():
    """Clear entire prediction history (admin action)."""
    count = Prediction.query.count()
    Prediction.query.delete()
    db.session.commit()
    flash(f"All {count} predictions deleted.", "warning")
    return redirect(url_for("history.index"))


@history_bp.route("/export-csv")
def export_csv():
    """Export all predictions (or filtered set) as a CSV download."""
    search = request.args.get("search", "").strip()
    result_filter = request.args.get("result", "")

    query = Prediction.query
    if search:
        query = query.filter(Prediction.applicant_name.ilike(f"%{search}%"))
    if result_filter in ("Approved", "Rejected"):
        query = query.filter_by(result=result_filter)

    predictions = query.order_by(Prediction.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Date", "Applicant Name", "Email", "Age", "Gender",
        "Annual Income", "Credit Score", "Employment Status",
        "Loan Amount", "Loan Term", "Loan Purpose",
        "Result", "Probability (%)", "Confidence (%)",
        "Risk Score", "Credit Rating", "Model Used",
    ])
    for p in predictions:
        writer.writerow([
            p.id,
            p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "",
            p.applicant_name,
            p.applicant_email or "",
            p.age or "",
            p.gender or "",
            p.annual_income or "",
            p.credit_score or "",
            p.employment_status or "",
            p.loan_amount or "",
            p.loan_term or "",
            p.loan_purpose or "",
            p.result,
            f"{p.probability * 100:.1f}" if p.probability else "",
            p.confidence or "",
            p.risk_score or "",
            p.credit_rating or "",
            p.model_used or "",
        ])

    output.seek(0)
    filename = f"predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@history_bp.route("/view/<int:pred_id>")
def view(pred_id: int):
    """Redirect to the full result page for a prediction."""
    return redirect(url_for("predict.result", pred_id=pred_id))
