"""
run.py
Application entry point. Run with: python run.py
"""

import os
import logging
from app import create_app

# ── Create app instance ────────────────────────────────────────────────────────
app = create_app(os.environ.get("FLASK_ENV", "development"))


if __name__ == "__main__":
    # Configure basic logging to stdout when running directly
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")

    app.logger.info(f"Starting Credit Card Approval Prediction App on {host}:{port}")
    app.logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")

    app.run(
        host=host,
        port=port,
        debug=app.config.get("DEBUG", True),
        use_reloader=True,
    )
