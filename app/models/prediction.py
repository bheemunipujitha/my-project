"""
app/models/prediction.py
SQLAlchemy model for storing prediction records in SQLite.
"""

from datetime import datetime, timezone
from app import db


class Prediction(db.Model):
    """Stores every credit card approval prediction made through the app."""

    __tablename__ = "predictions"

    # ── Primary Key ────────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # ── Applicant Identity ─────────────────────────────────────────────────
    applicant_name = db.Column(db.String(100), nullable=False, default="Anonymous")
    applicant_email = db.Column(db.String(150), nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    marital_status = db.Column(db.String(20), nullable=True)
    num_children = db.Column(db.Integer, nullable=True)
    education = db.Column(db.String(30), nullable=True)

    # ── Financial Details ─────────────────────────────────────────────────
    annual_income = db.Column(db.Float, nullable=True)
    total_assets = db.Column(db.Float, nullable=True)
    total_debt = db.Column(db.Float, nullable=True)
    credit_score = db.Column(db.Integer, nullable=True)
    net_worth = db.Column(db.Float, nullable=True)

    # ── Employment Details ─────────────────────────────────────────────────
    employment_status = db.Column(db.String(30), nullable=True)
    years_employed = db.Column(db.Float, nullable=True)
    occupation = db.Column(db.String(50), nullable=True)

    # ── Loan Information ───────────────────────────────────────────────────
    loan_amount = db.Column(db.Float, nullable=True)
    loan_term = db.Column(db.Integer, nullable=True)
    loan_purpose = db.Column(db.String(50), nullable=True)

    # ── Credit History ─────────────────────────────────────────────────────
    months_customer = db.Column(db.Integer, nullable=True)
    has_default = db.Column(db.Boolean, nullable=True, default=False)
    prior_loans = db.Column(db.Integer, nullable=True)

    # ── Prediction Output ──────────────────────────────────────────────────
    result = db.Column(db.String(20), nullable=False)           # "Approved" / "Rejected"
    probability = db.Column(db.Float, nullable=True)            # 0.0 – 1.0
    confidence = db.Column(db.Float, nullable=True)             # 0.0 – 100.0
    risk_score = db.Column(db.Float, nullable=True)             # 0 – 100
    credit_rating = db.Column(db.String(10), nullable=True)     # AAA, AA, A, BBB, BB, B, CCC
    recommendation = db.Column(db.Text, nullable=True)
    risk_factors = db.Column(db.Text, nullable=True)            # JSON-serialised list
    positive_factors = db.Column(db.Text, nullable=True)        # JSON-serialised list
    model_used = db.Column(db.String(50), nullable=True, default="XGBoost")
    source = db.Column(db.String(20), nullable=True, default="web")  # web / api

    # ── Metadata ───────────────────────────────────────────────────────────
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<Prediction #{self.id} | {self.applicant_name} | {self.result}>"

    def to_dict(self) -> dict:
        """Serialise to a JSON-safe dictionary for the API."""
        import json
        return {
            "id": self.id,
            "applicant_name": self.applicant_name,
            "applicant_email": self.applicant_email,
            "gender": self.gender,
            "age": self.age,
            "annual_income": self.annual_income,
            "credit_score": self.credit_score,
            "employment_status": self.employment_status,
            "loan_amount": self.loan_amount,
            "result": self.result,
            "probability": self.probability,
            "confidence": self.confidence,
            "risk_score": self.risk_score,
            "credit_rating": self.credit_rating,
            "recommendation": self.recommendation,
            "risk_factors": json.loads(self.risk_factors) if self.risk_factors else [],
            "positive_factors": json.loads(self.positive_factors) if self.positive_factors else [],
            "model_used": self.model_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @property
    def is_approved(self) -> bool:
        return self.result == "Approved"

    @property
    def formatted_income(self) -> str:
        if self.annual_income:
            return f"₹{self.annual_income:,.0f}"
        return "N/A"

    @property
    def formatted_loan(self) -> str:
        if self.loan_amount:
            return f"₹{self.loan_amount:,.0f}"
        return "N/A"

    @property
    def credit_rating_badge_color(self) -> str:
        """Return Bootstrap badge color class for the credit rating."""
        rating_colors = {
            "AAA": "success", "AA": "success", "A": "success",
            "BBB": "info", "BB": "warning",
            "B": "warning", "CCC": "danger", "D": "danger",
        }
        return rating_colors.get(self.credit_rating, "secondary")
