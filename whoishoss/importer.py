"""Load HOSS source files from data/hoss/ into the whoishoss SQLite DB."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .extensions import db
from .models import HossConfig, HossProfile, HossQuestion, HossRun, HossTrainingSample


DATA_SUBDIR = Path("data") / "hoss"


def _data_dir(project_root: Path) -> Path:
    return project_root / DATA_SUBDIR


def _upsert_config(name: str, document: Any) -> None:
    row = HossConfig.query.filter_by(name=name).one_or_none()
    payload = json.dumps(document, ensure_ascii=False)
    if row is None:
        db.session.add(HossConfig(name=name, document_json=payload))
    else:
        row.document_json = payload


def import_hoss_config(project_root: Path) -> None:
    base = _data_dir(project_root)
    for fname in ("hoss_labels.json", "hoss_agent.example.json"):
        path = base / fname
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as f:
            doc = json.load(f)
        _upsert_config(name=path.stem, document=doc)


def import_hoss_questions(project_root: Path) -> None:
    path = _data_dir(project_root) / "f_scale_questions.json"
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        rows = json.load(f)
    for row in rows:
        qid = int(row["id"])
        rec = HossQuestion.query.get(qid)
        if rec is None:
            rec = HossQuestion(id=qid)
            db.session.add(rec)
        rec.text = row["text"]
        rec.scale_min = int(row.get("scale_min", 1))
        rec.scale_max = int(row.get("scale_max", 6))


def _item_keys_from_csv_row(row: dict[str, str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for i in range(1, 31):
        key = f"item_{i:02d}"
        if key in row and row[key] != "":
            try:
                out[key] = int(row[key])
            except ValueError:
                continue
    return out


def _upsert_training_sample(rec: dict[str, Any]) -> None:
    name = rec["name"]
    source = rec["source"]
    existing = HossTrainingSample.query.filter_by(name=name, source=source).one_or_none()

    items = rec.get("f_scale_items") or {}
    traits = rec.get("traits") or {}

    values = dict(
        name=name,
        source=source,
        input_summary=rec.get("input_summary"),
        f_scale_items_json=json.dumps(items, ensure_ascii=False),
        square=float(traits.get("square", rec.get("square", 0.0))),
        punisher=float(traits.get("punisher", rec.get("punisher", 0.0))),
        power=float(traits.get("power", rec.get("power", 0.0))),
        skull=float(traits.get("skull", rec.get("skull", 0.0))),
        hoss_score=float(rec.get("hoss_score", 0.0)),
        hoss_level=int(rec.get("hoss_level", 0)),
        display_label=rec.get("display_label", ""),
        internal_label=rec.get("internal_label", ""),
        explanation=rec.get("explanation"),
    )

    if existing is None:
        db.session.add(HossTrainingSample(**values))
    else:
        for k, v in values.items():
            setattr(existing, k, v)


def import_hoss_training_jsonl(project_root: Path) -> int:
    path = _data_dir(project_root) / "hoss_training_samples.jsonl"
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            _upsert_training_sample(rec)
            count += 1
    return count


def import_hoss_training_csv(project_root: Path) -> int:
    """Fallback import from CSV if the JSONL file is absent."""
    path = _data_dir(project_root) / "hoss_training_samples.csv"
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rec: dict[str, Any] = {
                "name": row["name"],
                "source": row["source"],
                "input_summary": row.get("input_summary"),
                "explanation": row.get("explanation"),
                "hoss_score": row.get("hoss_score"),
                "hoss_level": row.get("hoss_level"),
                "display_label": row.get("display_label"),
                "internal_label": row.get("internal_label"),
                "traits": {
                    "square": row.get("square"),
                    "punisher": row.get("punisher"),
                    "power": row.get("power"),
                    "skull": row.get("skull"),
                },
                "f_scale_items": _item_keys_from_csv_row(row),
            }
            _upsert_training_sample(rec)
            count += 1
    return count


def import_hoss_dataset(project_root: Path, *, force: bool = False) -> None:
    """Idempotent full import. If force=True, wipe HOSS data first (keeps profiles/runs)."""
    if force:
        HossTrainingSample.query.delete()
        HossQuestion.query.delete()
        HossConfig.query.delete()
        db.session.commit()

    import_hoss_config(project_root)
    import_hoss_questions(project_root)
    inserted = import_hoss_training_jsonl(project_root)
    if inserted == 0:
        import_hoss_training_csv(project_root)

    db.session.commit()


def ensure_hoss_dataset_loaded(project_root: Path) -> None:
    """Only load if the DB is empty — cheap to call on every startup."""
    has_labels = HossConfig.query.filter_by(name="hoss_labels").one_or_none() is not None
    has_questions = db.session.query(HossQuestion.id).first() is not None
    has_samples = db.session.query(HossTrainingSample.id).first() is not None
    if has_labels and has_questions and has_samples:
        return
    import_hoss_dataset(project_root, force=False)


__all__ = [
    "HossProfile",
    "HossRun",
    "import_hoss_dataset",
    "ensure_hoss_dataset_loaded",
]
