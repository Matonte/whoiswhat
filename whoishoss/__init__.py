"""WhoIsHoss microservice — HOSS (F-scale archetype) classifier.

Runs as its own Flask app with its own SQLAlchemy db instance and its own
SQLite database, so it is a true sibling microservice to `whoiswhat`.
"""

import os
from pathlib import Path

import click
from dotenv import load_dotenv
from flask import Flask, current_app

from .extensions import db
from .routes import bp as hoss_bp


def create_app() -> Flask:
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env", override=True)

    database_url = os.getenv("HOSS_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "HOSS_DATABASE_URL (or DATABASE_URL fallback) is not set. "
            "Copy .env.example to .env and set HOSS_DATABASE_URL."
        )

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    app.register_blueprint(hoss_bp)
    _register_cli(app)

    return app


def _register_cli(app: Flask) -> None:
    @app.cli.command("import-hoss-data")
    @click.option(
        "--force",
        is_flag=True,
        help="Clear HOSS config, questions, and training samples, then reload from data/hoss.",
    )
    def import_hoss_data_cmd(force: bool) -> None:
        from .importer import import_hoss_dataset

        root = Path(current_app.root_path).parent
        import_hoss_dataset(root, force=force)
        click.echo("import-hoss-data complete.")
