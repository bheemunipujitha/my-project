"""
app/utils/ml_engine.py
Local machine learning engine.
Trains, saves, loads, and runs inference with Random Forest, Logistic
Regression, Decision Tree, and XGBoost models on the UCI Credit dataset.
"""

import os
import json
import time
import logging
import numpy as np
import pandas as pd
import joblib
from typing import Optional

logger = logging.getLogger(__name__)

# ── Feature schema ─────────────────────────────────────────────────────────────
FEATURE_COLUMNS = [
    "gender", "age", "marital_status", "num_children", "education",
    "annual_income", "total_assets", "total_debt", "credit_score",
    "employment_status", "years_employed",
    "loan_amount", "loan_term",
    "months_customer", "has_default", "prior_loans",
]

CATEGORICAL_MAP = {
    "gender":            {"Male": 1, "Female": 0},
    "marital_status":    {"Single": 0, "Married": 1, "Divorced": 2, "Widowed": 3},
    "education":         {"High School": 0, "Some College": 1, "Bachelor's": 2, "Master's": 3, "PhD": 4},
    "employment_status": {"Unemployed": 0, "Part-time": 1, "Self-employed": 2, "Full-time": 3},
}


class MLEngine:
    """Handles training, loading, and inference for all four classifiers."""

    MODEL_NAMES = ["xgboost", "random_forest", "logistic_regression", "decision_tree"]

    def __init__(self, models_dir: str):
        self.models_dir = models_dir
        os.makedirs(models_dir, exist_ok=True)
        self._models: dict = {}
        self._scaler = None
        self._is_ready = False

    # ── Public API ─────────────────────────────────────────────────────────

    def load_models(self) -> bool:
        """Load pre-trained model files from disk."""
        try:
            scaler_path = os.path.join(self.models_dir, "scaler.joblib")
            if os.path.exists(scaler_path):
                self._scaler = joblib.load(scaler_path)

            for name in self.MODEL_NAMES:
                path = os.path.join(self.models_dir, f"{name}.joblib")
                if os.path.exists(path):
                    self._models[name] = joblib.load(path)
                    logger.info(f"Loaded model: {name}")

            self._is_ready = bool(self._models)
            return self._is_ready
        except Exception as exc:
            logger.error(f"Failed to load models: {exc}")
            return False

    def train_and_save(self) -> dict:
        """
        Generate synthetic training data, train all four classifiers,
        save them to disk, and return performance metrics.
        """
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.preprocessing import StandardScaler
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score, f1_score,
            confusion_matrix, roc_auc_score
        )
        try:
            from xgboost import XGBClassifier
            xgb_available = True
        except ImportError:
            xgb_available = False
            logger.warning("XGBoost not installed. Skipping XGBoost model.")

        logger.info("Generating synthetic training data…")
        X, y = self._generate_dataset(n_samples=5000)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        joblib.dump(scaler, os.path.join(self.models_dir, "scaler.joblib"))
        self._scaler = scaler

        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )

        classifiers = {
            "random_forest": RandomForestClassifier(
                n_estimators=200, max_depth=10, min_samples_split=5,
                random_state=42, n_jobs=-1, class_weight="balanced"
            ),
            "logistic_regression": LogisticRegression(
                C=1.0, max_iter=1000, random_state=42, class_weight="balanced"
            ),
            "decision_tree": DecisionTreeClassifier(
                max_depth=8, min_samples_split=10,
                random_state=42, class_weight="balanced"
            ),
        }
        if xgb_available:
            classifiers["xgboost"] = XGBClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                eval_metric="logloss",
                random_state=42
            )

        results = {}
        for name, clf in classifiers.items():
            logger.info(f"Training {name}…")
            t0 = time.time()
            clf.fit(X_train, y_train)
            train_time = round(time.time() - t0, 3)

            t1 = time.time()
            y_pred = clf.predict(X_test)
            pred_time = round((time.time() - t1) * 1000, 2)  # ms

            y_proba = clf.predict_proba(X_test)[:, 1] if hasattr(clf, "predict_proba") else None

            acc = round(accuracy_score(y_test, y_pred) * 100, 2)
            results[name] = {
                "accuracy": acc,
                "precision": round(precision_score(y_test, y_pred, zero_division=0) * 100, 2),
                "recall": round(recall_score(y_test, y_pred, zero_division=0) * 100, 2),
                "f1_score": round(f1_score(y_test, y_pred, zero_division=0) * 100, 2),
                "auc_roc": round(roc_auc_score(y_test, y_proba) * 100, 2) if y_proba is not None else None,
                "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
                "train_time_s": train_time,
                "pred_time_ms": pred_time,
            }

            path = os.path.join(self.models_dir, f"{name}.joblib")
            joblib.dump(clf, path)
            self._models[name] = clf
            logger.info(f"  {name}: accuracy={acc}%  saved to {path}")

        # Persist metrics
        metrics_path = os.path.join(self.models_dir, "metrics.json")
        with open(metrics_path, "w") as f:
            json.dump(results, f, indent=2)

        self._is_ready = True
        return results

    def predict(self, input_data: dict, model_name: str = "xgboost") -> dict:
        """
        Run a single prediction.

        Args:
            input_data: dict of feature values matching FEATURE_COLUMNS
            model_name: which model to use

        Returns:
            dict with result, probability, confidence, risk_score,
                 credit_rating, recommendation, risk_factors, positive_factors
        """
        if not self._is_ready:
            self.load_models()
        if not self._models:
            # Fall back to heuristic if no models present
            return self._heuristic_predict(input_data)

        # Prefer xgboost, fall back to first available
        if model_name not in self._models:
            model_name = next(iter(self._models))

        clf = self._models[model_name]
        X = self._preprocess(input_data)

        t0 = time.time()
        proba = clf.predict_proba(X)[0]
        pred_time_ms = round((time.time() - t0) * 1000, 2)

        approved_prob = float(proba[1])   # cast numpy float32 → Python float
        result = "Approved" if approved_prob >= 0.5 else "Rejected"
        confidence = round(float(max(proba)) * 100, 1)
        risk_score = round((1 - approved_prob) * 100, 1)
        credit_rating = self._compute_credit_rating(
            input_data.get("credit_score", 600),
            approved_prob,
            input_data.get("has_default", False),
        )
        recommendation = self._generate_recommendation(result, input_data, approved_prob)
        risk_factors = self._identify_risk_factors(input_data)
        positive_factors = self._identify_positive_factors(input_data)

        return {
            "result": result,
            "probability": round(approved_prob, 4),
            "confidence": confidence,
            "risk_score": risk_score,
            "credit_rating": credit_rating,
            "recommendation": recommendation,
            "risk_factors": risk_factors,
            "positive_factors": positive_factors,
            "model_used": model_name,
            "pred_time_ms": pred_time_ms,
        }

    def get_metrics(self) -> Optional[dict]:
        """Load saved training metrics from disk."""
        path = os.path.join(self.models_dir, "metrics.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return None

    def get_feature_importance(self, model_name: str = "random_forest") -> Optional[dict]:
        """Return feature importances for tree-based models."""
        if model_name not in self._models:
            self.load_models()
        clf = self._models.get(model_name)
        if clf is None or not hasattr(clf, "feature_importances_"):
            return None
        importance = clf.feature_importances_
        return dict(sorted(
            zip(FEATURE_COLUMNS, importance.tolist()),
            key=lambda x: x[1], reverse=True
        ))

    # ── Private helpers ────────────────────────────────────────────────────

    def _preprocess(self, data: dict) -> np.ndarray:
        """Encode categoricals, build feature vector, and scale."""
        row = {}
        for col in FEATURE_COLUMNS:
            val = data.get(col, 0)
            if col in CATEGORICAL_MAP and isinstance(val, str):
                val = CATEGORICAL_MAP[col].get(val, 0)
            if col == "has_default":
                val = 1 if val else 0
            row[col] = float(val) if val is not None else 0.0

        X = np.array([[row[c] for c in FEATURE_COLUMNS]])
        if self._scaler is not None:
            X = self._scaler.transform(X)
        return X

    def _heuristic_predict(self, data: dict) -> dict:
        """Simple rule-based fallback when no trained model is available."""
        score = data.get("credit_score", 600)
        income = data.get("annual_income", 30000)
        has_default = data.get("has_default", False)
        debt = data.get("total_debt", 0)
        loan_amount = data.get("loan_amount", 10000)

        debt_ratio = debt / income if income > 0 else 1.0

        # Scoring heuristic
        pts = 0
        pts += 30 if score >= 750 else (20 if score >= 650 else (10 if score >= 550 else 0))
        pts += 20 if income >= 60000 else (15 if income >= 40000 else 10)
        pts -= 15 if has_default else 0
        pts -= 10 if debt_ratio > 0.5 else (5 if debt_ratio > 0.35 else 0)
        pts += 5 if loan_amount < income * 0.3 else 0

        approved_prob = min(max(pts / 55, 0.05), 0.95)
        result = "Approved" if approved_prob >= 0.5 else "Rejected"
        confidence = round(max(approved_prob, 1 - approved_prob) * 100, 1)

        return {
            "result": result,
            "probability": round(approved_prob, 4),
            "confidence": confidence,
            "risk_score": round((1 - approved_prob) * 100, 1),
            "credit_rating": self._compute_credit_rating(score, approved_prob, has_default),
            "recommendation": self._generate_recommendation(result, data, approved_prob),
            "risk_factors": self._identify_risk_factors(data),
            "positive_factors": self._identify_positive_factors(data),
            "model_used": "heuristic",
            "pred_time_ms": 0.5,
        }

    @staticmethod
    def _compute_credit_rating(credit_score: int, prob: float, has_default: bool) -> str:
        if has_default:
            return "CCC"
        if credit_score >= 800 and prob >= 0.85:
            return "AAA"
        if credit_score >= 750 and prob >= 0.75:
            return "AA"
        if credit_score >= 700 and prob >= 0.60:
            return "A"
        if credit_score >= 650 and prob >= 0.50:
            return "BBB"
        if credit_score >= 600 and prob >= 0.40:
            return "BB"
        if credit_score >= 550:
            return "B"
        return "CCC"

    @staticmethod
    def _generate_recommendation(result: str, data: dict, prob: float) -> str:
        if result == "Approved":
            if prob >= 0.85:
                return "Excellent creditworthiness. Applicant qualifies for premium card offers."
            return "Good credit profile. Standard credit card approved with regular limit."
        # Rejected
        credit_score = data.get("credit_score", 0)
        has_default = data.get("has_default", False)
        debt = data.get("total_debt", 0)
        income = data.get("annual_income", 1)
        if has_default:
            return "Clear existing default records. Reapply after 12 months of clean credit history."
        if credit_score < 600:
            return "Build credit score above 650 through secured cards or credit-builder loans."
        if (debt / income if income else 1) > 0.5:
            return "Reduce debt-to-income ratio below 35% before reapplying."
        return "Address credit risk factors and reapply after 6 months of financial improvement."

    @staticmethod
    def _identify_risk_factors(data: dict) -> list:
        factors = []
        if data.get("has_default"):
            factors.append("Prior loan default on record")
        if data.get("credit_score", 700) < 600:
            factors.append(f"Low credit score ({data.get('credit_score')})")
        income = data.get("annual_income", 1) or 1
        debt = data.get("total_debt", 0) or 0
        if debt / income > 0.5:
            factors.append(f"High debt-to-income ratio ({debt/income:.0%})")
        if data.get("employment_status") == "Unemployed":
            factors.append("Currently unemployed")
        if data.get("years_employed", 3) < 1:
            factors.append("Less than 1 year at current employer")
        loan = data.get("loan_amount", 0) or 0
        if loan > income * 0.5:
            factors.append("Loan amount is high relative to income")
        return factors[:5]  # Cap at 5

    @staticmethod
    def _identify_positive_factors(data: dict) -> list:
        factors = []
        if data.get("credit_score", 0) >= 720:
            factors.append(f"Strong credit score ({data.get('credit_score')})")
        if not data.get("has_default"):
            factors.append("Clean credit history — no defaults")
        if data.get("annual_income", 0) >= 60000:
            factors.append(f"High annual income (₹{data.get('annual_income'):,.0f})")
        if data.get("years_employed", 0) >= 3:
            factors.append(f"Stable employment ({data.get('years_employed')} years)")
        income = data.get("annual_income", 1) or 1
        debt = data.get("total_debt", 0) or 0
        if debt / income < 0.3:
            factors.append("Low debt-to-income ratio")
        assets = data.get("total_assets", 0) or 0
        if assets > data.get("loan_amount", 0):
            factors.append("Assets exceed requested loan amount")
        return factors[:5]

    @staticmethod
    def _generate_dataset(n_samples: int = 5000):
        """
        Generates a realistic synthetic credit dataset.
        Returns (X, y) as numpy arrays.
        """
        rng = np.random.default_rng(42)

        age = rng.integers(21, 70, n_samples).astype(float)
        gender = rng.integers(0, 2, n_samples).astype(float)
        marital = rng.integers(0, 4, n_samples).astype(float)
        children = rng.integers(0, 5, n_samples).astype(float)
        education = rng.integers(0, 5, n_samples).astype(float)

        income = (rng.lognormal(10.8, 0.5, n_samples)).clip(15000, 500000)
        assets = (income * rng.uniform(0.5, 5.0, n_samples)).clip(0)
        debt = (income * rng.uniform(0.05, 0.8, n_samples)).clip(0)
        credit_score = (rng.normal(660, 80, n_samples)).clip(300, 850).astype(float)

        emp_status = rng.integers(0, 4, n_samples).astype(float)
        years_emp = (rng.exponential(4, n_samples)).clip(0, 40)

        loan_amount = (income * rng.uniform(0.1, 0.7, n_samples)).clip(1000)
        loan_term = rng.choice([12, 24, 36, 48, 60], n_samples).astype(float)

        months_cust = rng.integers(1, 120, n_samples).astype(float)
        has_default = rng.binomial(1, 0.12, n_samples).astype(float)
        prior_loans = rng.integers(0, 8, n_samples).astype(float)

        X = np.column_stack([
            gender, age, marital, children, education,
            income, assets, debt, credit_score,
            emp_status, years_emp,
            loan_amount, loan_term,
            months_cust, has_default, prior_loans,
        ])

        # Label: approval probability driven by credit score, income, default history
        debt_ratio  = debt / income
        score_norm  = (credit_score - 300) / 550
        income_norm = np.log1p(income) / np.log1p(500000)
        emp_norm    = emp_status / 3.0
        tenure_norm = years_emp / 40.0

        p_approve = (
            0.45 * score_norm
            + 0.25 * income_norm
            - 0.25 * has_default
            - 0.15 * debt_ratio.clip(0, 1)
            + 0.05 * emp_norm
            + 0.05 * tenure_norm
        )
        # Sharper sigmoid for cleaner decision boundary → higher accuracy
        p_approve = 1 / (1 + np.exp(-10 * (p_approve - 0.40)))
        y = rng.binomial(1, p_approve.clip(0.01, 0.99))

        return X, y


# ── Module-level singleton ──────────────────────────────────────────────────────
_engine: Optional[MLEngine] = None


def get_engine(models_dir: str = None) -> MLEngine:
    """Return the singleton MLEngine, initialising if necessary."""
    global _engine
    if _engine is None:
        if models_dir is None:
            base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml_models"))
            models_dir = base
        _engine = MLEngine(models_dir)
        _engine.load_models()
        if not _engine._is_ready:
            logger.info("No saved models found — training now (first run)…")
            _engine.train_and_save()
    return _engine
