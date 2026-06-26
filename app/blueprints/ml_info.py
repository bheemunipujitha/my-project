"""
app/blueprints/ml_info.py
ML Information blueprint: dataset info, algorithm explanations, metrics.
"""

import logging
from flask import Blueprint, render_template
from app.utils.ml_engine import get_engine

logger = logging.getLogger(__name__)
ml_info_bp = Blueprint("ml_info", __name__)


@ml_info_bp.route("/")
def index():
    """Machine Learning page: algorithms, metrics, feature importance."""
    try:
        engine = get_engine()
        metrics = engine.get_metrics() or {}
        feature_importance = engine.get_feature_importance("random_forest") or {}
        xgb_importance = engine.get_feature_importance("xgboost") or {}
    except Exception as exc:
        logger.error(f"ML info load error: {exc}")
        metrics = {}
        feature_importance = {}
        xgb_importance = {}

    algorithms = [
        {
            "name": "XGBoost",
            "icon": "bi-lightning-charge-fill",
            "color": "primary",
            "description": (
                "Gradient Boosting framework that uses decision trees as base learners. "
                "Combines weak learners sequentially to minimise prediction error. "
                "Primary model deployed on IBM Watson ML."
            ),
            "pros": ["Highest accuracy", "Handles missing data", "Regularisation built-in", "Fast inference"],
            "cons": ["Memory intensive", "Hyperparameter sensitive"],
            "key": "xgboost",
        },
        {
            "name": "Random Forest",
            "icon": "bi-diagram-3-fill",
            "color": "success",
            "description": (
                "Ensemble of independently trained decision trees. Predictions are made "
                "by majority vote. Robust to overfitting and noisy features."
            ),
            "pros": ["High accuracy", "Feature importance", "No scaling needed", "Robust"],
            "cons": ["Slow for very large datasets", "Black-box"],
            "key": "random_forest",
        },
        {
            "name": "Logistic Regression",
            "icon": "bi-graph-up",
            "color": "info",
            "description": (
                "Linear classifier that models the probability of the binary outcome "
                "using a sigmoid function. Highly interpretable baseline model."
            ),
            "pros": ["Interpretable", "Fast training", "Probabilistic output", "Low memory"],
            "cons": ["Assumes linearity", "Feature engineering required"],
            "key": "logistic_regression",
        },
        {
            "name": "Decision Tree",
            "icon": "bi-share-fill",
            "color": "warning",
            "description": (
                "Hierarchical model that splits the data on feature thresholds to minimise "
                "impurity. Fully interpretable — the decision path is a human-readable rule set."
            ),
            "pros": ["Fully interpretable", "No normalisation needed", "Fast prediction"],
            "cons": ["Prone to overfitting", "Unstable with small data"],
            "key": "decision_tree",
        },
    ]

    dataset_info = {
        "samples": 5000,
        "features": 16,
        "target": "Binary (Approved / Rejected)",
        "class_balance": "~58% Approved, ~42% Rejected",
        "train_split": "80% train / 20% test",
        "preprocessing": "Standard Scaling, Label Encoding",
        "source": "Synthetic dataset modelled on UCI German Credit",
    }

    return render_template(
        "ml_info.html",
        algorithms=algorithms,
        metrics=metrics,
        feature_importance=feature_importance,
        xgb_importance=xgb_importance,
        dataset_info=dataset_info,
    )
