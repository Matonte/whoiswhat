"""Development server for the WhoIsHoss microservice.

Usage (from project root):
    python run_whoishoss.py        # default port 5002

Override with PORT env var.
"""

import os
from pathlib import Path

from whoishoss import create_app
from whoishoss.extensions import db
from whoishoss.importer import ensure_hoss_dataset_loaded

app = create_app()

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent
    with app.app_context():
        db.create_all()
        ensure_hoss_dataset_loaded(project_root)
    port = int(os.environ.get("PORT", "5002"))
    app.run(host="0.0.0.0", port=port, debug=True)
