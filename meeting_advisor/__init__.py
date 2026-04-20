"""Meeting Advisor microservice.

Aggregates WhoIsWhat (K taxonomy) + WhoIsHoss (HOSS F-scale) classifier
outputs for a named subject and asks an LLM for meeting-preparation
guidance given a user-supplied meeting context.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from .extensions import db
from .routes import bp as advisor_bp


def create_app() -> Flask:
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env", override=True)

    database_url = os.getenv("ADVISOR_DATABASE_URL") or "sqlite:///./meeting_advisor.db"

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["WHOISWHAT_URL"] = os.getenv("WHOISWHAT_URL", "http://127.0.0.1:5000")
    app.config["WHOISHOSS_URL"] = os.getenv("WHOISHOSS_URL", "http://127.0.0.1:5002")
    app.config["ADVISOR_CACHE_TTL_SECONDS"] = int(
        os.getenv("ADVISOR_CACHE_TTL_SECONDS", str(24 * 3600))
    )

    db.init_app(app)
    app.register_blueprint(advisor_bp)

    return app
