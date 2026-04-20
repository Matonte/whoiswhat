"""Models for the meeting_advisor service.

- `subject_cache` memoizes the two sibling-service classifier outputs for a
  given (subject_name, source_hint) so we don't re-classify on every request.
- `advice_runs` is the audit log of every /advise call.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .extensions import db


class SubjectCache(db.Model):
    __tablename__ = "subject_cache"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subject_name = db.Column(db.String(255), nullable=False)
    source_hint = db.Column(db.String(255), nullable=False, default="")
    k_profile_json = db.Column(db.Text)
    hoss_profile_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            "subject_name", "source_hint", name="uq_subject_cache_name_source"
        ),
    )

    def to_dict(self) -> dict[str, Any]:
        import json
        return {
            "subject_name": self.subject_name,
            "source_hint": self.source_hint,
            "k_profile": json.loads(self.k_profile_json) if self.k_profile_json else None,
            "hoss_profile": (
                json.loads(self.hoss_profile_json) if self.hoss_profile_json else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AdviceRun(db.Model):
    __tablename__ = "advice_runs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subject_name = db.Column(db.String(255), nullable=False)
    source_hint = db.Column(db.String(255))
    context_json = db.Column(db.Text, nullable=False)
    k_profile_json = db.Column(db.Text)
    hoss_profile_json = db.Column(db.Text)
    advice_json = db.Column(db.Text, nullable=False)
    risk_level = db.Column(db.String(16))
    model = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
