"""
app/utils/watson.py
IBM Watson Machine Learning integration.
Handles authentication, online deployment calls, and graceful fallback
to the local MLEngine when Watson credentials are not configured.
"""

import logging
import requests
from typing import Optional
from flask import current_app

logger = logging.getLogger(__name__)

# IBM IAM token endpoint
IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"


class WatsonMLClient:
    """
    Thin wrapper around the IBM Watson Machine Learning REST API.
    Authenticates with IAM and calls the online deployment endpoint.
    """

    def __init__(self, api_key: str, watson_url: str, deployment_id: str, space_id: str = ""):
        self.api_key = api_key
        self.watson_url = watson_url.rstrip("/")
        self.deployment_id = deployment_id
        self.space_id = space_id
        self._iam_token: Optional[str] = None

    # ── Public ─────────────────────────────────────────────────────────────

    def predict(self, input_features: list) -> dict:
        """
        Call the Watson ML online deployment endpoint.

        Args:
            input_features: List of feature values in the correct order.

        Returns:
            dict with 'result', 'probability', and raw Watson response.
        """
        token = self._get_iam_token()
        if not token:
            raise RuntimeError("IBM IAM authentication failed — check WATSON_API_KEY.")

        url = (
            f"{self.watson_url}/ml/v4/deployments/{self.deployment_id}"
            f"/predictions?version=2021-05-01"
        )
        payload = {
            "input_data": [
                {"values": [input_features]}
            ]
        }
        if self.space_id:
            payload["space_id"] = self.space_id

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        raw = resp.json()

        return self._parse_response(raw)

    # ── Private ────────────────────────────────────────────────────────────

    def _get_iam_token(self) -> Optional[str]:
        """Fetch a short-lived IBM IAM Bearer token using the API key."""
        if self._iam_token:
            return self._iam_token

        try:
            resp = requests.post(
                IAM_TOKEN_URL,
                data={
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                    "apikey": self.api_key,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=15,
            )
            resp.raise_for_status()
            self._iam_token = resp.json().get("access_token")
            return self._iam_token
        except Exception as exc:
            logger.error(f"IBM IAM token fetch failed: {exc}")
            return None

    @staticmethod
    def _parse_response(raw: dict) -> dict:
        """Parse Watson ML response into a standardised prediction dict."""
        try:
            predictions = raw["predictions"][0]
            values = predictions["values"][0]
            # Watson returns: [predicted_label, [prob_class_0, prob_class_1]]
            predicted_label = values[0]
            probabilities = values[1] if len(values) > 1 else [0.5, 0.5]

            approved_prob = float(probabilities[1]) if len(probabilities) > 1 else 0.5
            result = "Approved" if predicted_label in (1, "1", "Approved", True) else "Rejected"

            return {
                "result": result,
                "probability": round(approved_prob, 4),
                "raw_response": raw,
                "source": "watson",
            }
        except (KeyError, IndexError, TypeError) as exc:
            logger.error(f"Failed to parse Watson response: {exc}  |  raw={raw}")
            raise ValueError(f"Unexpected Watson ML response format: {exc}") from exc


# ── Factory helper ────────────────────────────────────────────────────────────

def get_watson_client() -> Optional[WatsonMLClient]:
    """
    Return a configured WatsonMLClient if credentials are set, else None.
    Caller should fall back to local MLEngine when this returns None.
    """
    api_key = current_app.config.get("WATSON_API_KEY", "")
    watson_url = current_app.config.get("WATSON_URL", "")
    deployment_id = current_app.config.get("WATSON_DEPLOYMENT_ID", "")
    space_id = current_app.config.get("WATSON_SPACE_ID", "")
    use_watson = current_app.config.get("USE_WATSON", False)

    if not use_watson or not api_key or not deployment_id:
        logger.debug("Watson ML not configured — using local model engine.")
        return None

    return WatsonMLClient(api_key, watson_url, deployment_id, space_id)
