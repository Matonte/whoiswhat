"""OpenAI classifier for the WhoIsHoss microservice.

Uses the canonical `hoss_classifier_system.txt` prompt shipped with the
starter files, injects a sample of DB-backed training examples and the
F-scale question bank, and returns the 30 item values. Actual scoring
(traits/score/level) is done deterministically by `scoring.py`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, OpenAIError

from .models import HossQuestion, HossTrainingSample


PROMPT_DIR = Path(__file__).resolve().parent.parent / "data" / "hoss"


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
                "OpenAI: insufficient quota. Add credits at "
                "https://platform.openai.com/account/billing and retry."
            )
        return f"OpenAI rate limit (429). {msg}"

    return f"OpenAI HTTP {exc.status_code}: {msg}"


def _load_prompt(name: str) -> str:
    path = PROMPT_DIR / name
    if not path.exists():
        raise RuntimeError(f"Prompt file missing: {path}")
    return path.read_text(encoding="utf-8")


def _question_bank() -> list[dict[str, Any]]:
    rows = HossQuestion.query.order_by(HossQuestion.id).all()
    return [r.to_dict() for r in rows]


def _training_examples(limit: int = 40) -> list[dict[str, Any]]:
    rows = (
        HossTrainingSample.query.order_by(HossTrainingSample.id).limit(limit).all()
    )
    return [r.to_dict() for r in rows]


def classify_hoss(
    name: str,
    source: str | None = None,
    input_summary: str | None = None,
    *,
    model: str | None = None,
) -> dict[str, Any]:
    """Ask the model to infer item_01..item_30 for the supplied subject.

    Returns the raw parsed JSON. Callers layer deterministic scoring on top.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or not api_key.strip():
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")

    classifier_prompt = _load_prompt("hoss_classifier_system.txt")

    questions = _question_bank()
    if not questions:
        raise RuntimeError(
            "F-scale question bank is empty. Run: flask --app whoishoss:create_app import-hoss-data"
        )

    examples = _training_examples()
    if not examples:
        raise RuntimeError(
            "HOSS training samples empty. Run: flask --app whoishoss:create_app import-hoss-data"
        )

    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    system = f"""{classifier_prompt}

QUESTION BANK (30 items on 1-6 scale; infer a value for EACH):
{json.dumps(questions, ensure_ascii=False)}

REFERENCE TRAINING SAMPLES (match calibration; do not copy verbatim):
{json.dumps(examples, ensure_ascii=False)}

Return a single JSON object with exactly these keys:
- "name": string
- "source": string (e.g. show/film/book; "self-report" or "invented" if none)
- "input_summary": string (1-2 sentence grounding summary you used)
- "f_scale_items": object mapping "item_01".."item_30" to integers 1-6 (all 30 keys required)
- "short_explanation": string, 2 short paragraphs max, grounded in observable behavior

Do not include traits, hoss_score, hoss_level, or labels; those are computed deterministically downstream.
Do not classify real private individuals; treat the output as a stylized fictional/archetypal classification.
"""

    subject_name = name.strip()
    src = (source or "").strip() or "invented"
    summary = (input_summary or "").strip()

    if summary:
        user = (
            f"Subject name: {subject_name}\n"
            f"Source / context: {src}\n\n"
            f"Summary / notes:\n{summary}\n\n"
            "Infer item_01..item_30 and provide a short grounded explanation."
        )
    else:
        user = (
            f"Subject name only: {subject_name}\n"
            f"Source / context: {src}\n\n"
            "No extra notes were provided. If the name refers to a well-known fictional character, "
            "use commonly known traits in the spirit of the reference samples. "
            "If the name is ambiguous or unfamiliar, infer conservatively and note the uncertainty "
            "in short_explanation. Infer item_01..item_30."
        )

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


def explain_hoss(
    name: str,
    source: str,
    traits: dict[str, float],
    hoss_score: float,
    display_label: str,
    short_explanation: str | None = None,
    *,
    model: str | None = None,
) -> str:
    """Optional step: use the explainer prompt to produce a polished 2-paragraph narrative."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return short_explanation or ""

    explainer_prompt = _load_prompt("hoss_explainer_system.txt")
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    user = (
        f"Subject: {name} ({source})\n"
        f"Traits: {json.dumps(traits)}\n"
        f"HOSS score: {hoss_score}\n"
        f"Display label: {display_label}\n"
    )
    if short_explanation:
        user += f"\nClassifier notes:\n{short_explanation}\n"

    client = OpenAI(api_key=api_key)
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": explainer_prompt},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
        )
    except OpenAIError:
        return short_explanation or ""

    return (completion.choices[0].message.content or "").strip() or (short_explanation or "")
