"""
app/blueprints/api.py
REST API blueprint: prediction, history, stats endpoints.
Swagger documentation available at /api/v1/docs
"""

import json
import logging
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models.prediction import Prediction
from app.utils.validators import validate_prediction_input

logger = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__)


def _api_response(data=None, message="", status=200, errors=None):
    """Standardised API response wrapper."""
    payload = {
        "status": "success" if status < 400 else "error",
        "message": message,
        "data": data,
    }
    if errors:
        payload["errors"] = errors
    return jsonify(payload), status


# ── Prediction ────────────────────────────────────────────────────────────────

@api_bp.route("/predict", methods=["POST"])
def predict():
    """
    POST /api/v1/predict
    Accepts JSON body with all prediction features.
    Returns prediction result with full analytics.
    ---
    Request body: { "applicant_name": str, "gender": str, ... }
    Response: { "result": "Approved|Rejected", "probability": float, ... }
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        return _api_response(message="Request body must be valid JSON.", status=400)

    is_valid, cleaned = validate_prediction_input(data)
    if not is_valid:
        return _api_response(message="Validation failed.", status=422, errors=cleaned)

    from app.blueprints.predict import _run_prediction
    result_data = _run_prediction(cleaned)

    # Persist to DB
    prediction = _save_prediction(cleaned, result_data, source="api")

    response_data = {
        "prediction_id": prediction.id,
        **result_data,
    }
    return _api_response(data=response_data, message="Prediction completed.", status=200)


@api_bp.route("/predict/batch", methods=["POST"])
def predict_batch():
    """
    POST /api/v1/predict/batch
    Accepts a JSON array of applicant records.
    Returns an array of prediction results.
    """
    records = request.get_json(force=True, silent=True)
    if not isinstance(records, list):
        return _api_response(message="Expected a JSON array of applicant records.", status=400)

    if len(records) > 100:
        return _api_response(message="Batch size must not exceed 100 records.", status=400)

    from app.blueprints.predict import _run_prediction
    results = []
    for i, record in enumerate(records):
        is_valid, cleaned = validate_prediction_input(record)
        if not is_valid:
            results.append({"index": i, "status": "error", "errors": cleaned})
            continue
        result_data = _run_prediction(cleaned)
        prediction = _save_prediction(cleaned, result_data, source="api_batch")
        results.append({"index": i, "prediction_id": prediction.id, **result_data})

    return _api_response(data={"results": results, "count": len(results)})


# ── History ───────────────────────────────────────────────────────────────────

@api_bp.route("/history", methods=["GET"])
def history():
    """
    GET /api/v1/history?page=1&per_page=20&result=Approved
    Returns paginated prediction history.
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    result_filter = request.args.get("result", "")

    query = Prediction.query
    if result_filter in ("Approved", "Rejected"):
        query = query.filter_by(result=result_filter)

    pagination = query.order_by(Prediction.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return _api_response(data={
        "predictions": [p.to_dict() for p in pagination.items],
        "total":   pagination.total,
        "page":    pagination.page,
        "pages":   pagination.pages,
        "per_page": per_page,
    })


@api_bp.route("/history/<int:pred_id>", methods=["GET"])
def history_detail(pred_id: int):
    """GET /api/v1/history/:id — Single prediction record."""
    p = Prediction.query.get_or_404(pred_id)
    return _api_response(data=p.to_dict())


@api_bp.route("/history/<int:pred_id>", methods=["DELETE"])
def history_delete(pred_id: int):
    """DELETE /api/v1/history/:id — Remove a prediction record."""
    p = Prediction.query.get_or_404(pred_id)
    db.session.delete(p)
    db.session.commit()
    return _api_response(message=f"Prediction #{pred_id} deleted.")


# ── Statistics ────────────────────────────────────────────────────────────────

@api_bp.route("/stats", methods=["GET"])
def stats():
    """GET /api/v1/stats — Aggregate application statistics."""
    from app.blueprints.dashboard import _get_stats
    return _api_response(data=_get_stats())


# ── Model Info ────────────────────────────────────────────────────────────────

@api_bp.route("/model/info", methods=["GET"])
def model_info():
    """GET /api/v1/model/info — ML model metadata and metrics."""
    from app.utils.ml_engine import get_engine
    try:
        engine = get_engine()
        metrics = engine.get_metrics() or {}
        fi = engine.get_feature_importance("random_forest") or {}
    except Exception as exc:
        return _api_response(message=f"Model info unavailable: {exc}", status=500)

    return _api_response(data={
        "primary_model":      current_app.config.get("PRIMARY_MODEL", "xgboost"),
        "watson_enabled":     current_app.config.get("USE_WATSON", False),
        "metrics":            metrics,
        "feature_importance": fi,
    })


# ── Health ────────────────────────────────────────────────────────────────────

@api_bp.route("/health", methods=["GET"])
def health():
    """GET /api/v1/health — Liveness check."""
    return _api_response(data={
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": current_app.config.get("APP_VERSION", "1.0.0"),
    })


# ── Docs ──────────────────────────────────────────────────────────────────────

@api_bp.route("/docs", methods=["GET"])
def docs():
    """Minimal inline Swagger UI."""
    from flask import render_template_string
    html = """<!DOCTYPE html>
<html>
<head>
  <title>Credit Approval API — Docs</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({
      url: "/api/v1/openapi.json",
      dom_id: "#swagger-ui",
      presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
      layout: "BaseLayout",
    });
  </script>
</body>
</html>"""
    return render_template_string(html)


@api_bp.route("/openapi.json", methods=["GET"])
def openapi_spec():
    """Minimal OpenAPI 3.0 spec."""
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Credit Card Approval Prediction API",
            "version": "1.0.0",
            "description": "REST API for credit card approval predictions powered by IBM Watson ML."
        },
        "paths": {
            "/api/v1/predict": {
                "post": {
                    "summary": "Single credit prediction",
                    "tags": ["Prediction"],
                    "requestBody": {"required": True, "content": {"application/json": {
                        "schema": {"$ref": "#/components/schemas/PredictionInput"}
                    }}},
                    "responses": {"200": {"description": "Prediction result"}}
                }
            },
            "/api/v1/history": {
                "get": {"summary": "Paginated prediction history", "tags": ["History"],
                        "responses": {"200": {"description": "List of predictions"}}}
            },
            "/api/v1/stats": {
                "get": {"summary": "Aggregate statistics", "tags": ["Stats"],
                        "responses": {"200": {"description": "KPI stats"}}}
            },
            "/api/v1/health": {
                "get": {"summary": "Health check", "tags": ["Health"],
                        "responses": {"200": {"description": "OK"}}}
            },
        },
        "components": {
            "schemas": {
                "PredictionInput": {
                    "type": "object",
                    "required": ["gender", "age", "annual_income", "credit_score",
                                 "employment_status", "loan_amount", "loan_term", "loan_purpose"],
                    "properties": {
                        "applicant_name":   {"type": "string", "example": "Rahul Sharma"},
                        "gender":           {"type": "string", "enum": ["Male", "Female"]},
                        "age":              {"type": "integer", "minimum": 18, "maximum": 75},
                        "marital_status":   {"type": "string"},
                        "education":        {"type": "string"},
                        "annual_income":    {"type": "number"},
                        "total_assets":     {"type": "number"},
                        "total_debt":       {"type": "number"},
                        "credit_score":     {"type": "integer"},
                        "employment_status": {"type": "string"},
                        "years_employed":   {"type": "number"},
                        "loan_amount":      {"type": "number"},
                        "loan_term":        {"type": "integer"},
                        "loan_purpose":     {"type": "string"},
                        "has_default":      {"type": "boolean"},
                        "prior_loans":      {"type": "integer"},
                    }
                }
            }
        }
    }
    return jsonify(spec)


# ── Helper ────────────────────────────────────────────────────────────────────

def _save_prediction(cleaned: dict, result_data: dict, source: str = "api") -> Prediction:
    """Persist a prediction record to the database and return the instance."""
    prediction = Prediction(
        applicant_name    = cleaned.get("applicant_name", "API User"),
        applicant_email   = cleaned.get("applicant_email"),
        gender            = cleaned.get("gender"),
        age               = cleaned.get("age"),
        marital_status    = cleaned.get("marital_status"),
        num_children      = cleaned.get("num_children"),
        education         = cleaned.get("education"),
        annual_income     = cleaned.get("annual_income"),
        total_assets      = cleaned.get("total_assets"),
        total_debt        = cleaned.get("total_debt"),
        credit_score      = cleaned.get("credit_score"),
        net_worth         = cleaned.get("net_worth"),
        employment_status = cleaned.get("employment_status"),
        years_employed    = cleaned.get("years_employed"),
        occupation        = cleaned.get("occupation"),
        loan_amount       = cleaned.get("loan_amount"),
        loan_term         = cleaned.get("loan_term"),
        loan_purpose      = cleaned.get("loan_purpose"),
        months_customer   = cleaned.get("months_customer"),
        has_default       = cleaned.get("has_default"),
        prior_loans       = cleaned.get("prior_loans"),
        result            = result_data["result"],
        probability       = result_data["probability"],
        confidence        = result_data["confidence"],
        risk_score        = result_data["risk_score"],
        credit_rating     = result_data["credit_rating"],
        recommendation    = result_data["recommendation"],
        risk_factors      = json.dumps(result_data.get("risk_factors", [])),
        positive_factors  = json.dumps(result_data.get("positive_factors", [])),
        model_used        = result_data.get("model_used", "XGBoost"),
        source            = source,
        ip_address        = request.remote_addr,
        user_agent        = request.headers.get("User-Agent", "")[:255],
    )
    db.session.add(prediction)
    db.session.commit()
    return prediction
