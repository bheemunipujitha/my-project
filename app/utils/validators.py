"""
app/utils/validators.py
Input validation helpers for the prediction form and REST API.
Returns structured error dicts so both Flask routes and the API
can reuse the same validation logic.
"""

from typing import Tuple


def validate_prediction_input(data: dict) -> Tuple[bool, dict]:
    """
    Validate and sanitise prediction form data.

    Args:
        data: Raw form/JSON input dictionary.

    Returns:
        (is_valid: bool, cleaned_data_or_errors: dict)
        If invalid, the second element maps field names to error messages.
    """
    errors = {}

    # ── Helper functions ───────────────────────────────────────────────────
    def require_int(field, min_val, max_val, label):
        val = data.get(field)
        try:
            v = int(val)
            if not (min_val <= v <= max_val):
                errors[field] = f"{label} must be between {min_val} and {max_val}."
                return None
            return v
        except (TypeError, ValueError):
            errors[field] = f"{label} is required and must be a whole number."
            return None

    def require_float(field, min_val, max_val, label):
        val = data.get(field)
        try:
            v = float(val)
            if not (min_val <= v <= max_val):
                errors[field] = f"{label} must be between {min_val:,} and {max_val:,}."
                return None
            return v
        except (TypeError, ValueError):
            errors[field] = f"{label} is required and must be a number."
            return None

    def require_choice(field, choices, label):
        val = data.get(field, "").strip()
        if val not in choices:
            errors[field] = f"{label} must be one of: {', '.join(choices)}."
            return None
        return val

    def optional_float(field, min_val, max_val, label):
        val = data.get(field)
        if val in (None, "", "0"):
            return 0.0
        try:
            v = float(val)
            if not (min_val <= v <= max_val):
                errors[field] = f"{label} must be between {min_val:,} and {max_val:,}."
                return None
            return v
        except (TypeError, ValueError):
            errors[field] = f"{label} must be a number."
            return None

    # ── Personal Information ───────────────────────────────────────────────
    applicant_name = data.get("applicant_name", "Anonymous").strip() or "Anonymous"
    if len(applicant_name) > 100:
        errors["applicant_name"] = "Name must not exceed 100 characters."

    gender = require_choice("gender", ["Male", "Female"], "Gender")
    age = require_int("age", 18, 75, "Age")
    marital_status = require_choice(
        "marital_status",
        ["Single", "Married", "Divorced", "Widowed"],
        "Marital Status"
    )
    num_children = require_int("num_children", 0, 10, "Number of Children")
    education = require_choice(
        "education",
        ["High School", "Some College", "Bachelor's", "Master's", "PhD"],
        "Education Level"
    )

    # ── Financial Details ──────────────────────────────────────────────────
    annual_income = require_float("annual_income", 5000, 10_000_000, "Annual Income")
    total_assets = optional_float("total_assets", 0, 100_000_000, "Total Assets")
    total_debt = optional_float("total_debt", 0, 10_000_000, "Total Debt")
    credit_score = require_int("credit_score", 300, 850, "Credit Score")

    # ── Employment Details ─────────────────────────────────────────────────
    employment_status = require_choice(
        "employment_status",
        ["Full-time", "Part-time", "Self-employed", "Unemployed"],
        "Employment Status"
    )
    years_employed = optional_float("years_employed", 0, 50, "Years Employed")
    occupation = data.get("occupation", "").strip()[:50]

    # ── Loan Information ───────────────────────────────────────────────────
    loan_amount = require_float("loan_amount", 500, 5_000_000, "Loan Amount")
    loan_term = require_int("loan_term", 6, 360, "Loan Term (months)")
    loan_purpose = require_choice(
        "loan_purpose",
        ["Personal", "Home", "Auto", "Education", "Business", "Medical", "Other"],
        "Loan Purpose"
    )

    # ── Credit History ─────────────────────────────────────────────────────
    months_customer = optional_float("months_customer", 0, 600, "Months as Customer")
    has_default_raw = data.get("has_default", "false")
    has_default = has_default_raw in (True, "true", "True", "1", 1, "yes", "Yes")
    prior_loans = require_int("prior_loans", 0, 50, "Prior Loans")

    if errors:
        return False, errors

    cleaned = {
        "applicant_name": applicant_name,
        "applicant_email": data.get("applicant_email", "").strip()[:150],
        "gender": gender,
        "age": age,
        "marital_status": marital_status,
        "num_children": num_children,
        "education": education,
        "annual_income": annual_income,
        "total_assets": total_assets,
        "total_debt": total_debt,
        "credit_score": credit_score,
        "net_worth": (total_assets or 0) - (total_debt or 0),
        "employment_status": employment_status,
        "years_employed": years_employed,
        "occupation": occupation,
        "loan_amount": loan_amount,
        "loan_term": loan_term,
        "loan_purpose": loan_purpose,
        "months_customer": months_customer,
        "has_default": has_default,
        "prior_loans": prior_loans,
    }
    return True, cleaned
