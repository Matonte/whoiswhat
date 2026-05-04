"""Separate SQLAlchemy instance for the whoishoss service.

Kept distinct from `contact_advisor.extensions.db` so the services can run as
independent processes with independent databases.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
