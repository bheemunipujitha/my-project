"""
app/blueprints/predict.py
Prediction blueprint: form submission, result display, PDF download, email.
"""

import json
import logging
from flask import (
    Blueprint, render_template, request, flash, redirect,
    url_for, session, send_file, current_app, jsonify
)
import io

from app import db
from app.models.prediction import Prediction
from app.utils.validators import validate_prediction_input
from app.utils.ml_engine import get_engine
from app.utils.watson import get_watson_client

logger = logging.getLogger(__name__)
predict_bp = Blueprint("predict", __name__)


@predict_bp.route("/", methods=["GET"])
def form():
    """Render the multi-section prediction form."""
    return render_template("predict.html")


@predict_bp.route("/submit", methods=["POST"])
def submit():
    """
    Handle prediction form submission.
    1. Validate inputs
    2. Run prediction (Watson → local engine fallback)
    3. Save to DB
    4. Redirect to result page
    """
    raw = request.form.to_dict()
    is_valid, data = validate_prediction_input(raw)

    if not is_valid:
        # data contains field→error mapping
        for field, msg in data.items():
            flash(f"{field.replace('_', ' ').title()}: {msg}", "danger")
        return redirect(url_for("predict.form"))

    # ── Run prediction ─────────────────────────────────────────────────────
    result_data = _run_prediction(data)

    # ── Persist to SQLite ──────────────────────────────────────────────────
    prediction = Prediction(
        applicant_name    = data["applicant_name"],
        applicant_email   = data.get("applicant_email"),
        gender            = data["gender"],
        age               = data["age"],
        marital_status    = data["marital_status"],
        num_children      = data["num_children"],
        education         = data["education"],
        annual_income     = data["annual_income"],
        total_assets      = data["total_assets"],
        total_debt        = data["total_debt"],
        credit_score      = data["credit_score"],
        net_worth         = data["net_worth"],
        employment_status = data["employment_status"],
        years_employed    = data["years_employed"],
        occupation        = data.get("occupation"),
        loan_amount       = data["loan_amount"],
        loan_term         = data["loan_term"],
        loan_purpose      = data["loan_purpose"],
        months_customer   = data["months_customer"],
        has_default       = data["has_default"],
        prior_loans       = data["prior_loans"],
        result            = result_data["result"],
        probability       = result_data["probability"],
        confidence        = result_data["confidence"],
        risk_score        = result_data["risk_score"],
        credit_rating     = result_data["credit_rating"],
        recommendation    = result_data["recommendation"],
        risk_factors      = json.dumps(result_data.get("risk_factors", [])),
        positive_factors  = json.dumps(result_data.get("positive_factors", [])),
        model_used        = result_data.get("model_used", "XGBoost"),
        source            = "web",
        ip_address        = request.remote_addr,
        user_agent        = request.headers.get("User-Agent", "")[:255],
    )
    db.session.add(prediction)
    db.session.commit()

    # Store prediction ID in session for PDF/email actions
    session["last_prediction_id"] = prediction.id
    return redirect(url_for("predict.result", pred_id=prediction.id))


@predict_bp.route("/result/<int:pred_id>")
def result(pred_id: int):
    """Display the rich result dashboard for a specific prediction."""
    prediction = Prediction.query.get_or_404(pred_id)

    risk_factors     = json.loads(prediction.risk_factors)     if prediction.risk_factors     else []
    positive_factors = json.loads(prediction.positive_factors) if prediction.positive_factors else []

    # Build radar chart data (6 dimensions)
    radar_data = _build_radar_data(prediction)

    return render_template(
        "result.html",
        p=prediction,
        risk_factors=risk_factors,
        positive_factors=positive_factors,
        radar_data=radar_data,
    )


@predict_bp.route("/download-pdf/<int:pred_id>")
def download_pdf(pred_id: int):
    """Generate and stream a PDF report for the prediction."""
    prediction = Prediction.query.get_or_404(pred_id)
    from app.utils.pdf_generator import generate_prediction_pdf

    pdf_bytes = generate_prediction_pdf(prediction)
    if not pdf_bytes:
        flash("PDF generation requires the ReportLab library.", "warning")
        return redirect(url_for("predict.result", pred_id=pred_id))

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"credit_report_{pred_id}.pdf",
    )


@predict_bp.route("/send-email/<int:pred_id>", methods=["POST"])
def send_email(pred_id: int):
    """Email the prediction result to the applicant's address."""
    prediction = Prediction.query.get_or_404(pred_id)
    email = request.form.get("email") or prediction.applicant_email

    if not email:
        flash("No email address provided.", "danger")
        return redirect(url_for("predict.result", pred_id=pred_id))

    from app.utils.email_service import send_prediction_email
    success = send_prediction_email(prediction, email)

    if success:
        flash(f"Result emailed to {email} successfully.", "success")
    else:
        flash("Failed to send email. Check your mail configuration.", "danger")

    return redirect(url_for("predict.result", pred_id=pred_id))


# ── Private helpers ────────────────────────────────────────────────────────────

def _run_prediction(data: dict) -> dict:
    """Try Watson ML first; fall back to local engine."""
    try:
        watson = get_watson_client()
        if watson:
            from app.utils.ml_engine import FEATURE_COLUMNS, CATEGORICAL_MAP

            # Build ordered feature vector
            feature_vector = []
            for col in FEATURE_COLUMNS:
                val = data.get(col, 0)
                if col in CATEGORICAL_MAP and isinstance(val, str):
                    val = CATEGORICAL_MAP[col].get(val, 0)
                if col == "has_default":
                    val = 1 if val else 0
                feature_vector.append(float(val) if val is not None else 0.0)

            watson_result = watson.predict(feature_vector)
            # Enrich Watson result with local engine post-processing
            engine = get_engine()
            local_partial = engine._heuristic_predict(data)
            return {
                **local_partial,
                "result": watson_result["result"],
                "probability": watson_result["probability"],
                "model_used": "IBM Watson ML",
                "source": "watson",
            }
    except Exception as exc:
        logger.warning(f"Watson prediction failed, falling back to local engine: {exc}")

    # Local engine
    engine = get_engine()
    return engine.predict(data, model_name=current_app.config.get("PRIMARY_MODEL", "xgboost"))


def _build_radar_data(p: Prediction) -> dict:
    """Compute 0–100 scores for six credit dimensions for the radar chart."""
    income = p.annual_income or 0
    debt = p.total_debt or 0

    credit_health    = min(100, max(0, (p.credit_score - 300) / 5.5)) if p.credit_score else 50
    income_strength  = min(100, income / 1000)
    debt_management  = max(0, 100 - (debt / income * 100)) if income > 0 else 50
    employment_score = min(100, (p.years_employed or 0) * 10)
    loan_capacity    = max(0, 100 - ((p.loan_amount or 0) / income * 100)) if income > 0 else 50
    history_score    = max(0, 80 - (20 if p.has_default else 0) + min(20, (p.months_customer or 0) / 6))

    return {
        "labels": ["Credit Health", "Income Strength", "Debt Management",
                   "Employment", "Loan Capacity", "Credit History"],
        "values": [
            round(credit_health, 1),
            round(income_strength, 1),
            round(debt_management, 1),
            round(min(100, employment_score), 1),
            round(min(100, loan_capacity), 1),
            round(min(100, history_score), 1),
        ]
    }
