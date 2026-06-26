"""
tests/test_app.py
Basic unit and integration tests for the Flask application.
Run: pytest tests/ -v
"""

import pytest
import json


@pytest.fixture
def app():
    """Create application instance for testing."""
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from app import create_app
    application = create_app('testing')
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


# ── Route Tests ────────────────────────────────────────────────────────────────

class TestMainRoutes:
    def test_homepage(self, client):
        r = client.get('/')
        assert r.status_code == 200
        assert b'CreditPredict' in r.data or b'Credit' in r.data

    def test_about(self, client):
        r = client.get('/about')
        assert r.status_code == 200

    def test_contact_get(self, client):
        r = client.get('/contact')
        assert r.status_code == 200

    def test_404(self, client):
        r = client.get('/nonexistent-page-xyz')
        assert r.status_code == 404


class TestPredictRoutes:
    def test_predict_form(self, client):
        r = client.get('/predict/')
        assert r.status_code == 200

    def test_predict_submit_invalid(self, client):
        """Missing required fields should redirect back."""
        r = client.post('/predict/submit', data={}, follow_redirects=True)
        assert r.status_code == 200


class TestAPIRoutes:
    def test_health(self, client):
        r = client.get('/api/v1/health')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['data']['status'] == 'ok'

    def test_history_empty(self, client):
        r = client.get('/api/v1/history')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert 'predictions' in data['data']

    def test_stats(self, client):
        r = client.get('/api/v1/stats')
        assert r.status_code == 200

    def test_predict_api_missing_fields(self, client):
        r = client.post('/api/v1/predict',
                        data=json.dumps({}),
                        content_type='application/json')
        assert r.status_code in (400, 422)

    def test_predict_api_valid(self, client):
        payload = {
            "applicant_name": "Test User",
            "gender": "Male",
            "age": 30,
            "marital_status": "Single",
            "num_children": 0,
            "education": "Bachelor's",
            "annual_income": 600000,
            "total_assets": 1000000,
            "total_debt": 100000,
            "credit_score": 720,
            "employment_status": "Full-time",
            "years_employed": 5,
            "loan_amount": 200000,
            "loan_term": 36,
            "loan_purpose": "Personal",
            "months_customer": 24,
            "has_default": False,
            "prior_loans": 1,
        }
        r = client.post('/api/v1/predict',
                        data=json.dumps(payload),
                        content_type='application/json')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['data']['result'] in ('Approved', 'Rejected')
        assert 0 <= data['data']['probability'] <= 1


# ── Validator Tests ────────────────────────────────────────────────────────────

class TestValidators:
    def test_valid_input(self):
        from app.utils.validators import validate_prediction_input
        data = {
            "gender": "Male", "age": "30", "marital_status": "Single",
            "num_children": "0", "education": "Bachelor's",
            "annual_income": "600000", "total_assets": "1000000",
            "total_debt": "100000", "credit_score": "720",
            "employment_status": "Full-time", "years_employed": "5",
            "loan_amount": "200000", "loan_term": "36",
            "loan_purpose": "Personal", "has_default": "false",
            "prior_loans": "1",
        }
        valid, result = validate_prediction_input(data)
        assert valid is True
        assert result['credit_score'] == 720

    def test_invalid_credit_score(self):
        from app.utils.validators import validate_prediction_input
        data = {"credit_score": "99"}  # below 300
        valid, errors = validate_prediction_input(data)
        assert valid is False
        assert 'credit_score' in errors

    def test_invalid_age(self):
        from app.utils.validators import validate_prediction_input
        data = {"age": "15"}  # below 18
        valid, errors = validate_prediction_input(data)
        assert valid is False


# ── ML Engine Tests ────────────────────────────────────────────────────────────

class TestMLEngine:
    def test_heuristic_predict(self):
        from app.utils.ml_engine import MLEngine
        engine = MLEngine('/tmp/test_models')
        result = engine._heuristic_predict({
            "credit_score": 720,
            "annual_income": 600000,
            "has_default": False,
            "total_debt": 50000,
            "loan_amount": 100000,
        })
        assert result['result'] in ('Approved', 'Rejected')
        assert 0 <= result['probability'] <= 1
        assert result['credit_rating'] in ('AAA','AA','A','BBB','BB','B','CCC')

    def test_generate_dataset(self):
        from app.utils.ml_engine import MLEngine
        X, y = MLEngine._generate_dataset(200)
        assert X.shape == (200, 16)
        assert set(y).issubset({0, 1})
