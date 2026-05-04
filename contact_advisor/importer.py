"""Load K taxonomy + training files from data/raw into the database."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .extensions import db
from .models import DatasetSchema, TaxonomyEdge, TaxonomyNode, TrainingExample


def _raw_dir(project_root: Path) -> Path:
    return project_root / "data" / "raw"


def import_dataset_schemas(project_root: Path) -> None:
    raw = _raw_dir(project_root)
    schema_path = raw / "k_training_schema.json"
    graph_path = raw / "k_taxonomy_graph.json"

    if schema_path.is_file():
        body = schema_path.read_text(encoding="utf-8")
        meta = json.loads(body)
        name = meta.get("dataset_name", "k_training_schema")
        ver = meta.get("version")
        _upsert_schema(name, ver, body)

    if graph_path.is_file():
        body = graph_path.read_text(encoding="utf-8")
        _upsert_schema("k_taxonomy_graph", None, body)


def _upsert_schema(name: str, version: str | None, document_json: str) -> None:
    row = DatasetSchema.query.filter_by(name=name).one_or_none()
    if row is None:
        row = DatasetSchema(name=name, version=version, document_json=document_json)
        db.session.add(row)
    else:
        row.version = version
        row.document_json = document_json


def import_taxonomy_from_graph_json(project_root: Path, *, force: bool = False) -> None:
    raw = _raw_dir(project_root)
    path = raw / "k_taxonomy_graph.json"
    if not path.is_file():
        return

    if not force and TaxonomyNode.query.count() > 0:
        return

    data = json.loads(path.read_text(encoding="utf-8"))
    nodes = data.get("nodes") or []
    edges = data.get("edges") or []

    TaxonomyEdge.query.delete()
    TaxonomyNode.query.delete()
    db.session.flush()

    for n in nodes:
        db.session.add(
            TaxonomyNode(
                node_id=n["node_id"],
                node_type=n["node_type"],
                label=n["label"],
                description=n.get("description") or "",
            )
        )
    for e in edges:
        db.session.add(
            TaxonomyEdge(
                source_node_id=e["source"],
                target_node_id=e["target"],
                relation=e["relation"],
            )
        )


def _row_to_example_dict(row: dict) -> dict:
    return {
        "example_id": row["example_id"].strip(),
        "subject_name": row["subject_name"].strip(),
        "subject_type": row["subject_type"].strip(),
        "source_universe": row["source_universe"].strip(),
        "classification_code": row["classification_code"].strip(),
        "classification_label": row["classification_label"].strip(),
        "awareness_failure_score": int(row["awareness_failure_score"]),
        "intent_failure_score": int(row["intent_failure_score"]),
        "control_failure_score": int(row["control_failure_score"]),
        "short_rationale": row["short_rationale"].strip(),
        "evidence_points": row["evidence_points"].strip(),
        "notes": (row.get("notes") or "").strip() or None,
    }


def _apply_example_dict(d: dict) -> None:
    ex = db.session.get(TrainingExample, d["example_id"])
    if ex is None:
        ex = TrainingExample(example_id=d["example_id"])
        db.session.add(ex)
    for key, val in d.items():
        if key == "example_id":
            continue
        setattr(ex, key, val)


def import_training_examples_jsonl(project_root: Path) -> None:
    path = _raw_dir(project_root) / "k_training_examples.jsonl"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        _apply_example_dict(json.loads(line))


def import_training_examples_csv(project_root: Path) -> None:
    path = _raw_dir(project_root) / "k_training_examples.csv"
    if not path.is_file():
        return
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("example_id"):
                continue
            _apply_example_dict(_row_to_example_dict(row))


def import_k_dataset(project_root: Path, *, force: bool = False) -> None:
    """
    Load evaluation schema, taxonomy graph, and training examples from data/raw.
    If force is True, taxonomy, training rows, and stored schema JSON are cleared first.
    """
    if force:
        TrainingExample.query.delete()
        TaxonomyEdge.query.delete()
        TaxonomyNode.query.delete()
        DatasetSchema.query.delete()
        db.session.flush()

    import_dataset_schemas(project_root)
    import_taxonomy_from_graph_json(project_root, force=force)
    import_training_examples_jsonl(project_root)
    import_training_examples_csv(project_root)
    db.session.commit()


def ensure_k_dataset_loaded(project_root: Path) -> None:
    """Idempotent: load from disk when taxonomy is empty."""
    if TaxonomyNode.query.count() > 0:
        return
    import_k_dataset(project_root, force=False)
