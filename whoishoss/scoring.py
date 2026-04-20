"""HOSS scoring pipeline.

Implements the algorithm documented in the HOSS starter README:

    items (30 values on 1-6) -> traits (square, punisher, power, skull)
                             -> hoss_score (weighted sum)
                             -> level + display_label + internal_label

All configuration (weights, thresholds, item mapping) is loaded from the
`hoss_labels` document in `hoss_config`, so the pipeline stays aligned
with the canonical config file shipped with the service.
"""

from __future__ import annotations

import json
from typing import Any, Iterable

from .models import HossConfig


def _item_key(i: int) -> str:
    return f"item_{i:02d}"


def load_labels_config() -> dict[str, Any]:
    row = HossConfig.query.filter_by(name="hoss_labels").one_or_none()
    if row is None:
        raise RuntimeError(
            "hoss_labels not loaded. Run: flask --app whoishoss:create_app import-hoss-data"
        )
    return json.loads(row.document_json)


def normalize_items(items: dict[str, Any] | Iterable[tuple[str, Any]]) -> dict[str, int]:
    """Accept either {'item_01': 4, ...} or {'1': 4} / {1: 4} and return the canonical form."""
    out: dict[str, int] = {}
    src = dict(items) if not isinstance(items, dict) else items
    for k, v in src.items():
        if isinstance(k, int):
            key = _item_key(k)
        else:
            k_str = str(k)
            if k_str.startswith("item_"):
                key = k_str
            else:
                try:
                    key = _item_key(int(k_str))
                except ValueError:
                    continue
        try:
            out[key] = int(v)
        except (TypeError, ValueError):
            continue
    return out


def compute_traits(items: dict[str, int], mapping: dict[str, list[int]]) -> dict[str, float]:
    """Average the 1-6 item responses for each dimension's item list."""

    def avg_for(ids: list[int]) -> float:
        vals = [items[_item_key(i)] for i in ids if _item_key(i) in items]
        return round(sum(vals) / len(vals), 2) if vals else 0.0

    return {
        "square": avg_for(mapping["square_items"]),
        "punisher": avg_for(mapping["punisher_items"]),
        "power": avg_for(mapping["power_items"]),
        "skull": avg_for(mapping["skull_items"]),
    }


def compute_hoss_score(traits: dict[str, float], weights: dict[str, float]) -> float:
    score = (
        weights["square"] * traits["square"]
        + weights["punisher"] * traits["punisher"]
        + weights["power"] * traits["power"]
        + weights["skull"] * traits["skull"]
    )
    return round(score, 2)


def map_to_level(score: float, thresholds: list[dict[str, Any]]) -> dict[str, Any]:
    for band in thresholds:
        if band["min_score"] <= score <= band["max_score"]:
            return {
                "hoss_level": band["level"],
                "display_label": band["display_label"],
                "internal_label": band["internal_label"],
            }
    last = thresholds[-1]
    return {
        "hoss_level": last["level"],
        "display_label": last["display_label"],
        "internal_label": last["internal_label"],
    }


def score_from_items(items: dict[str, Any]) -> dict[str, Any]:
    """Full pipeline: raw items dict -> canonical HOSS result fields."""
    cfg = load_labels_config()
    canon_items = normalize_items(items)
    traits = compute_traits(canon_items, cfg["dimension_mapping"])
    hoss_score = compute_hoss_score(traits, cfg["weights"])
    level_info = map_to_level(hoss_score, cfg["thresholds"])
    return {
        "f_scale_items": canon_items,
        "traits": traits,
        "hoss_score": hoss_score,
        **level_info,
    }
