"""Run the development server from the project root: python run.py

HOST / PORT env vars are honored (default 127.0.0.1:5000) so the same
entry point works locally and inside docker-compose.
"""

import os
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
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    app.run(host=host, port=port, debug=True)
