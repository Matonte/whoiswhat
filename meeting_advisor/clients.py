"""HTTP clients for the sibling classifier services.

Each client is defensive: it returns (profile_dict, error_str) so the
advisor can surface which service failed and keep going when one side
is unreachable or hit by an OpenAI rate limit.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

import requests
from flask import current_app

from .extensions import db
from .models import SubjectCache


DEFAULT_TIMEOUT = 60


def _url(service_config_key: str, path: str) -> str:
    base = current_app.config[service_config_key].rstrip("/")
    return f"{base}{path}"


def classify_k(subject_name: str, notes: str | None = None) -> tuple[dict[str, Any] | None, str | None]:
    """Call WhoIsWhat /api/v1/classify via HTTP."""
    payload: dict[str, Any] = {"subject_name": subject_name}
    if notes:
        payload["character"] = notes

    try:
        r = requests.post(
            _url("WHOISWHAT_URL", "/api/v1/classify"),
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )
    except requests.RequestException as e:
        return None, f"WhoIsWhat unreachable at {current_app.config['WHOISWHAT_URL']}: {e}"

    if r.status_code >= 400:
        try:
            body = r.json()
            msg = body.get("error") or body.get("detail") or r.text
        except ValueError:
            msg = r.text
        return None, f"WhoIsWhat HTTP {r.status_code}: {msg}"

    return r.json(), None


def _find_cached_hoss_profile(
    subject_name: str, source_hint: str
) -> dict[str, Any] | None:
    """Opportunistically reuse a matching HOSS profile already persisted
    by the whoishoss service (no need to burn another classify call)."""
    try:
        r = requests.get(
            _url("WHOISHOSS_URL", "/api/v1/hoss/profiles"),
            params={"limit": 200},
            timeout=15,
        )
        r.raise_for_status()
        rows = r.json()
    except (requests.RequestException, ValueError):
        return None

    name_lc = subject_name.strip().lower()
    source_lc = (source_hint or "").strip().lower()

    def _match(row: dict[str, Any]) -> bool:
        if (row.get("name") or "").strip().lower() != name_lc:
            return False
        if source_lc and (row.get("source") or "").strip().lower() != source_lc:
            return False
        return True

    matches = [row for row in rows if _match(row)]
    if not matches:
        return None

    pick = matches[0]

    try:
        detail = requests.get(
            _url("WHOISHOSS_URL", f"/api/v1/hoss/profiles/{pick['id']}"),
            timeout=15,
        )
        detail.raise_for_status()
        return detail.json()
    except (requests.RequestException, ValueError, KeyError):
        return None


def classify_hoss(
    subject_name: str,
    source_hint: str | None = None,
    notes: str | None = None,
    *,
    allow_cached: bool = True,
) -> tuple[dict[str, Any] | None, str | None]:
    """Reuse an existing HOSS profile if one matches; else classify fresh."""
    if allow_cached:
        cached = _find_cached_hoss_profile(subject_name, source_hint or "")
        if cached is not None:
            cached["_reused"] = True
            return cached, None

    payload: dict[str, Any] = {"name": subject_name}
    if source_hint:
        payload["source"] = source_hint
    if notes:
        payload["input_summary"] = notes

    try:
        r = requests.post(
            _url("WHOISHOSS_URL", "/api/v1/hoss/classify"),
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )
    except requests.RequestException as e:
        return None, f"WhoIsHoss unreachable at {current_app.config['WHOISHOSS_URL']}: {e}"

    if r.status_code >= 400:
        try:
            body = r.json()
            msg = body.get("error") or body.get("detail") or r.text
        except ValueError:
            msg = r.text
        return None, f"WhoIsHoss HTTP {r.status_code}: {msg}"

    return r.json(), None


def cache_lookup(subject_name: str, source_hint: str) -> SubjectCache | None:
    row = SubjectCache.query.filter_by(
        subject_name=subject_name, source_hint=source_hint or ""
    ).one_or_none()
    if row is None:
        return None

    ttl = current_app.config["ADVISOR_CACHE_TTL_SECONDS"]
    if row.updated_at and (datetime.utcnow() - row.updated_at) > timedelta(seconds=ttl):
        return None
    if not (row.k_profile_json and row.hoss_profile_json):
        return None
    return row


def cache_upsert(
    subject_name: str,
    source_hint: str,
    k_profile: dict[str, Any] | None,
    hoss_profile: dict[str, Any] | None,
) -> None:
    row = SubjectCache.query.filter_by(
        subject_name=subject_name, source_hint=source_hint or ""
    ).one_or_none()
    k_json = json.dumps(k_profile, ensure_ascii=False) if k_profile else None
    h_json = json.dumps(hoss_profile, ensure_ascii=False) if hoss_profile else None

    if row is None:
        db.session.add(
            SubjectCache(
                subject_name=subject_name,
                source_hint=source_hint or "",
                k_profile_json=k_json,
                hoss_profile_json=h_json,
            )
        )
    else:
        if k_json:
            row.k_profile_json = k_json
        if h_json:
            row.hoss_profile_json = h_json
    db.session.commit()
