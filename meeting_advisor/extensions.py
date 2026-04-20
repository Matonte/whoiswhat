"""Separate SQLAlchemy instance for the meeting_advisor service."""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
