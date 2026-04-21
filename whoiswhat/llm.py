"""Use OpenAI Chat Completions with criteria + training examples from the DB."""

from __future__ import annotations

import json
import os
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, OpenAIError

from .models import DatasetSchema, TrainingExample


def _openai_error_body_dict(exc: APIStatusError) -> dict[str, Any] | None:
    body: Any = exc.body
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            return None
    if not isinstance(body, dict):
        return None
    inner = body.get("error")
    return inner if isinstance(inner, dict) else None


def _openai_api_user_message(exc: APIStatusError) -> str:
    inner = _openai_error_body_dict(exc)
    api_msg = (inner or {}).get("message")
    code = (inner or {}).get("code") or (inner or {}).get("type")
    msg = str(api_msg).strip() if api_msg else str(exc.message).strip()

    if exc.status_code == 401:
        return f"OpenAI rejected the API key. {msg} Check OPENAI_API_KEY in your .env file."

    if exc.status_code == 429:
        if code == "insufficient_quota":
            return (
                "OpenAI: insufficient quota (no billable credits on this account or project). "
                "Add a payment method or buy credits: https://platform.openai.com/account/billing "
                "— then retry. You can also use an API key from another org that has quota."
            )
        return (
            f"OpenAI rate limit (429). {msg} "
            "If this persists, check usage limits at https://platform.openai.com/account/billing"
        )

    return f"OpenAI HTTP {exc.status_code}: {msg}"


def _criteria_document() -> dict[str, Any] | None:
    row = DatasetSchema.query.filter_by(name="k_taxonomy_training_examples").one_or_none()
    if row is None:
        return None
    return json.loads(row.document_json)


def _training_examples_payload(limit: int = 80) -> list[dict[str, Any]]:
    rows = TrainingExample.query.order_by(TrainingExample.example_id).limit(limit).all()
    return [r.to_dict() for r in rows]


def classify_subject(
    subject_name: str, character_summary: str | None = None, *, model: str | None = None
) -> dict[str, Any]:
    """
    Ask the model to assign a K taxonomy label and rationale using DB-backed criteria and examples.
    If character_summary is omitted or empty, the model uses the name plus general knowledge
    (as for well-known figures in the reference examples).
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or not api_key.strip():
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")

    criteria = _criteria_document()
    if criteria is None:
        raise RuntimeError("Evaluation criteria not loaded. Run import-k-data and ensure k_training_schema.json is in data/raw.")

    examples = _training_examples_payload()
    if not examples:
        raise RuntimeError("No training examples in the database. Run import-k-data.")

    model = (
        model
        or os.environ.get("WHOISWHAT_MODEL")
        or os.environ.get("OPENAI_MODEL")
        or "gpt-5.4-mini"
    )

    system = f"""You are an evaluator for a structured behavior-classification task.

Use ONLY the label_space codes (K0–K6) and human-readable labels exactly as defined in the criteria.
Score awareness_failure, intent_failure, and control_failure from 0–5 as described in the criteria dimensions.

CRITERIA (JSON):
{json.dumps(criteria, ensure_ascii=False)}

REFERENCE TRAINING EXAMPLES (JSON array — match style and rigor; do not copy IDs):
{json.dumps(examples, ensure_ascii=False)}

Respond with a single JSON object and no other text. Required keys:
- "classification_code": string, one of K0,K1,K2,K3,K4,K5,K6
- "classification_label": string (must match the criteria label_space for that code)
- "awareness_failure_score": integer 0-5
- "intent_failure_score": integer 0-5
- "control_failure_score": integer 0-5
- "short_rationale": string, 2-4 sentences explaining the assignment
"""

    name = subject_name.strip()
    extra = (character_summary or "").strip()
    if extra:
        user = f"""Subject name: {name}

Optional behavior notes: {extra}

Classify this subject according to the criteria and reference examples. Be concise and grounded in the notes and name."""
    else:
        user = f"""Subject name only: {name}

The user supplied only a name (no separate behavior summary). Use commonly known traits when this is a well-known fictional or public figure, in the spirit of the reference training examples. If the name is ambiguous or unfamiliar, classify conservatively and mention the uncertainty briefly in short_rationale.

Classify according to the criteria and reference examples."""

    client = OpenAI(api_key=api_key)
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
    except APIStatusError as e:
        raise RuntimeError(_openai_api_user_message(e)) from e
    except APIConnectionError as e:
        raise RuntimeError(
            "Cannot reach OpenAI (connection error). Check your network, firewall, or VPN."
        ) from e
    except APITimeoutError as e:
        raise RuntimeError("OpenAI request timed out. Try again in a moment.") from e
    except OpenAIError as e:
        raise RuntimeError(f"OpenAI error: {e}") from e

    raw = completion.choices[0].message.content
    if not raw:
        raise RuntimeError("Empty response from the model.")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "The model did not return valid JSON. Try again or set OPENAI_MODEL to another model."
        ) from e
