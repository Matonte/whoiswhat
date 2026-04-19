"""Run the development server from the project root: python run.py"""

from pathlib import Path

from whoiswhat import create_app
from whoiswhat.extensions import db
from whoiswhat.importer import ensure_k_dataset_loaded

app = create_app()

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent
    with app.app_context():
        db.create_all()
        ensure_k_dataset_loaded(project_root)
    app.run(debug=True)
