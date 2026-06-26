"""
app/utils/email_service.py
Email result sending using Flask-Mail.
"""

import logging
from flask import current_app, render_template_string
from flask_mail import Message
from app import mail

logger = logging.getLogger(__name__)

_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: 'Poppins', Arial, sans-serif; background: #F5F7FA; margin: 0; padding: 0; }
    .container { max-width: 600px; margin: 20px auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
    .header { background: #0F4C81; color: #fff; text-align: center; padding: 28px 20px; }
    .header h1 { margin: 0; font-size: 22px; }
    .header p  { margin: 6px 0 0; font-size: 13px; opacity: 0.85; }
    .result-banner { text-align: center; padding: 20px; background: {{ bg }}; color: #fff; }
    .result-banner h2 { margin: 0; font-size: 24px; }
    .body { padding: 24px 32px; }
    .metric-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 20px 0; }
    .metric { background: #F5F7FA; border-radius: 8px; padding: 14px; text-align: center; }
    .metric .val { font-size: 20px; font-weight: 700; color: #0F4C81; }
    .metric .lbl { font-size: 11px; color: #546E7A; margin-top: 4px; }
    .rec-box { background: #E3F2FD; border-left: 4px solid #1565C0; padding: 14px 16px; border-radius: 6px; margin: 16px 0; font-size: 13px; }
    .footer { background: #F5F7FA; text-align: center; padding: 16px; font-size: 11px; color: #90A4AE; }
  </style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>💳 Credit Card Approval Prediction</h1>
    <p>IBM Watson Machine Learning · Credit Risk Report</p>
  </div>
  <div class="result-banner" style="background: {{ bg }}">
    <h2>{{ icon }} Application {{ result }}</h2>
  </div>
  <div class="body">
    <p>Dear <strong>{{ name }}</strong>,</p>
    <p>Your credit card application has been evaluated. Here is your result summary:</p>
    <div class="metric-grid">
      <div class="metric"><div class="val">{{ prob }}%</div><div class="lbl">Approval Probability</div></div>
      <div class="metric"><div class="val">{{ confidence }}%</div><div class="lbl">Confidence</div></div>
      <div class="metric"><div class="val">{{ risk }}/100</div><div class="lbl">Risk Score</div></div>
      <div class="metric"><div class="val">{{ rating }}</div><div class="lbl">Credit Rating</div></div>
    </div>
    <div class="rec-box">{{ recommendation }}</div>
    <p style="font-size:12px; color:#546E7A;">
      Prediction ID: #{{ pred_id }} &nbsp;|&nbsp; Model: {{ model }}
    </p>
  </div>
  <div class="footer">
    Credit Card Approval Prediction System &nbsp;·&nbsp; IBM Watson ML<br>
    This is an automated message. Please do not reply.
  </div>
</div>
</body>
</html>
"""


def send_prediction_email(prediction, recipient_email: str) -> bool:
    """
    Send a prediction result email to the applicant.

    Args:
        prediction: Prediction ORM instance or dict.
        recipient_email: Destination email address.

    Returns:
        True if sent successfully, False otherwise.
    """
    try:
        def g(attr, default="N/A"):
            if isinstance(prediction, dict):
                return prediction.get(attr, default) or default
            return getattr(prediction, attr, default) or default

        is_approved = g("result") == "Approved"
        bg = "#2E7D32" if is_approved else "#D32F2F"
        icon = "✓" if is_approved else "✗"

        html_body = render_template_string(
            _EMAIL_TEMPLATE,
            bg=bg, icon=icon,
            result=g("result"),
            name=g("applicant_name", "Applicant"),
            prob=f"{float(g('probability', 0)) * 100:.1f}",
            confidence=g("confidence", "N/A"),
            risk=g("risk_score", "N/A"),
            rating=g("credit_rating", "N/A"),
            recommendation=g("recommendation", ""),
            pred_id=g("id", "N/A"),
            model=g("model_used", "XGBoost"),
        )

        msg = Message(
            subject=f"Your Credit Card Application Result — {g('result')}",
            recipients=[recipient_email],
            html=html_body,
        )
        mail.send(msg)
        logger.info(f"Prediction email sent to {recipient_email}")
        return True

    except Exception as exc:
        logger.error(f"Failed to send prediction email to {recipient_email}: {exc}")
        return False
