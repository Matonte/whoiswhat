"""Development server for the Meeting Advisor microservice.

Usage (from project root):
    python run_meeting_advisor.py      # default port 5003

The advisor calls the WhoIsWhat and WhoIsHoss services over HTTP
(defaults: http://127.0.0.1:5000 and http://127.0.0.1:5002). Override
with WHOISWHAT_URL / WHOISHOSS_URL env vars.
"""

import os

from meeting_advisor import create_app
from meeting_advisor.extensions import db

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", "5003"))
    app.run(host="0.0.0.0", port=port, debug=True)
