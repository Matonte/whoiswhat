"""SQLAlchemy models for the WhoIsHoss microservice.

Mirrors the `db/schema.sql` provided with the HOSS starter files and
adds tables for the question bank, training samples, and labels config
so the service is fully self-contained.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .extensions import db


class HossConfig(db.Model):
    """Key/value store for HOSS config documents (labels.json, agent config, etc.)."""

    __tablename__ = "hoss_config"

    name = db.Column(db.String(128), primary_key=True)
    document_json = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HossQuestion(db.Model):
    """One of the 30 F-scale-style items."""

    __tablename__ = "hoss_questions"

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    scale_min = db.Column(db.Integer, nullable=False, default=1)
    scale_max = db.Column(db.Integer, nullable=False, default=6)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "scale_min": self.scale_min,
            "scale_max": self.scale_max,
        }


class HossTrainingSample(db.Model):
    """Synthetic seed sample used as a reference example for the LLM."""

    __tablename__ = "hoss_training_samples"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    source = db.Column(db.String(255), nullable=False)
    input_summary = db.Column(db.Text)
    f_scale_items_json = db.Column(db.Text, nullable=False)
    square = db.Column(db.Float, nullable=False)
    punisher = db.Column(db.Float, nullable=False)
    power = db.Column(db.Float, nullable=False)
    skull = db.Column(db.Float, nullable=False)
    hoss_score = db.Column(db.Float, nullable=False)
    hoss_level = db.Column(db.Integer, nullable=False)
    display_label = db.Column(db.String(255), nullable=False)
    internal_label = db.Column(db.String(64), nullable=False)
    explanation = db.Column(db.Text)

    __table_args__ = (
        db.UniqueConstraint("name", "source", name="uq_hoss_sample_name_source"),
    )

    def to_dict(self) -> dict[str, Any]:
        import json
        return {
            "name": self.name,
            "source": self.source,
            "input_summary": self.input_summary,
            "f_scale_items": json.loads(self.f_scale_items_json),
            "traits": {
                "square": self.square,
                "punisher": self.punisher,
                "power": self.power,
                "skull": self.skull,
            },
            "hoss_score": self.hoss_score,
            "hoss_level": self.hoss_level,
            "display_label": self.display_label,
            "internal_label": self.internal_label,
            "explanation": self.explanation,
        }


class HossProfile(db.Model):
    """A produced classification result persisted for later retrieval."""

    __tablename__ = "hoss_profiles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    source = db.Column(db.String(255), nullable=False)
    input_summary = db.Column(db.Text)
    f_scale_items_json = db.Column(db.Text, nullable=False)
    square = db.Column(db.Float, nullable=False)
    punisher = db.Column(db.Float, nullable=False)
    power = db.Column(db.Float, nullable=False)
    skull = db.Column(db.Float, nullable=False)
    hoss_score = db.Column(db.Float, nullable=False)
    hoss_level = db.Column(db.Integer, nullable=False)
    display_label = db.Column(db.String(255), nullable=False)
    internal_label = db.Column(db.String(64), nullable=False)
    explanation = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class HossRun(db.Model):
    """Audit log of every classify call (raw request + raw response)."""

    __tablename__ = "hoss_runs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_name = db.Column(db.String(255))
    profile_source = db.Column(db.String(255))
    request_payload_json = db.Column(db.Text, nullable=False)
    response_payload_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
