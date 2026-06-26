"""app/models/__init__.py"""
from app.models.prediction import Prediction
from app.models.user import AdminUser

__all__ = ["Prediction", "AdminUser"]
