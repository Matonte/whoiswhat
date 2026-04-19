import os
from pathlib import Path

import click
from dotenv import load_dotenv
from flask import Flask, current_app

from .extensions import db
from .routes import bp as main_bp


def create_app():
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env", override=True)

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env in the project root."
        )

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    app.register_blueprint(main_bp)
    _register_cli(app)

    return app


def _register_cli(app: Flask) -> None:
    @app.cli.command("import-k-data")
    @click.option(
        "--force",
        is_flag=True,
        help="Clear taxonomy, training examples, and stored schema JSON, then reload from data/raw.",
    )
    def import_k_data_cmd(force: bool) -> None:
        from .importer import import_k_dataset

        root = Path(current_app.root_path).parent
        import_k_dataset(root, force=force)
        click.echo("import-k-data complete.")
