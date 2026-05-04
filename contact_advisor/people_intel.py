"""People intelligence workflow: public professional context only.

Callers (e.g. a job-hunt assistant) pass **pre-fetched** public text snippets.
This module does not scrape third-party sites; it synthesizes and flags
stakeholder signals from supplied evidence under strict safety rules.
"""

from __future__ import annotations

import json
import os
from typing import Any

from flask import Blueprint, jsonify, request
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, OpenAIError

bp = Blueprint("people_intel", __name__)


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

MAX_SNIPPET_CHARS = 24_000
MAX_SNIPPETS = 40


def _trim(s: str, limit: int) -> str:
    s = s.strip()
    if len(s) <= limit:
        return s
    return s[: limit - 3] + "..."


def analyze_public_professional_context(
    *,
    person: str,
    company: str | None,
    snippets: list[dict[str, str]],
    extra_notes: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Run the people-intel LLM workflow. Returns a single JSON object."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or not api_key.strip():
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")

    model = (
        model
        or os.environ.get("CONTACT_ADVISOR_PEOPLE_INTEL_MODEL")
        or os.environ.get("WHOISWHAT_PEOPLE_INTEL_MODEL")
        or os.environ.get("CONTACT_ADVISOR_MODEL")
        or os.environ.get("WHOISWHAT_MODEL")
        or os.environ.get("OPENAI_MODEL")
        or "gpt-5.4-mini"
    )

    capped = snippets[:MAX_SNIPPETS]
    per_snippet_cap = max(800, MAX_SNIPPET_CHARS // max(1, len(capped)))

    bundled: list[dict[str, str]] = []
    for i, row in enumerate(capped):
        label = str(row.get("source_label") or row.get("source") or f"source_{i + 1}").strip()
        content = _trim(str(row.get("content") or ""), per_snippet_cap)
        if not content:
            continue
        bundled.append({"source_label": label, "content": content})

    if not bundled:
        raise ValueError("At least one snippet with non-empty content is required.")

    system = """You are a professional-context analyst for recruiting/outreach prep.

PRODUCT FRAMING (use this language mentally; do not output medical or psychological labels):
- You summarize **public professional context** and **communication-style signals** observable from professional materials (how they write/speak about work in public), not personality, IQ, mental health, or private life.

ALLOWED SOURCE TYPES (callers label snippets; trust the label but only draw conclusions supported by the text):
LinkedIn summaries/job titles, employer bios/team pages, GitHub readmes or public repos, technical blogs, talk abstracts, conference speaker pages, public posts about work, podcasts/interviews about their role.

STRICTLY AVOID OR REFUSE TO INFER:
- Facebook or other clearly personal-only social feeds, family, relationships, children, home life
- Protected characteristics (race, religion, national origin, disability, age, sex/gender, etc.)
- Political affiliation, religion, sexual orientation
- Mental health, personality disorders, or "deep" psychological profiling
- Anything not grounded in the provided snippets—say so in professional_summary or use low confidence

TASK:
1. Identify who the subject appears to be in a **professional** sense (role, domain).
2. Summarize career-relevant background from the snippets only.
3. List **professional_interests** (work topics they emphasize publicly).
4. List **communication_style_signals**: short neutral descriptors tied to how they communicate *about work in public* (e.g. "technical", "narrative", "metrics-oriented")—never pop-psych or personality-disorder framing.
5. Estimate **stakeholder_likelihood** for decision_maker, recruiter, hiring_manager as numbers 0–1 based only on titles/activities in the text (not stereotypes). Use low values when uncertain.
6. Propose **safe_outreach_angle**: one concrete, respectful opening angle referencing public professional themes only—no manipulation, no private-life hooks.

Respond with a single JSON object and no other text. Required keys:
- "person": string (echo or normalize the supplied name)
- "likely_role": string
- "confidence": number 0–1 (your confidence in likely_role given evidence quality)
- "sources": array of strings (which source_label values you actually relied on; subset of input labels)
- "professional_interests": array of strings
- "communication_style_signals": array of strings (professional/public communication style only)
- "stakeholder_likelihood": object with keys "decision_maker", "recruiter", "hiring_manager" each a number 0–1
- "professional_summary": string, 2–5 sentences, grounded and cautious if data is thin
- "safe_outreach_angle": string, one sentence
Optional keys (include when useful):
- "limitations": string, e.g. missing LinkedIn or thin evidence
"""

    user_obj: dict[str, Any] = {
        "person": person.strip(),
        "company": (company or "").strip() or None,
        "public_source_snippets": bundled,
        "notes_for_model": (extra_notes or "").strip() or None,
    }
    user = json.dumps(user_obj, ensure_ascii=False, indent=2)

    client = OpenAI(api_key=api_key)
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=0.25,
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
            "The model did not return valid JSON. Try again or set CONTACT_ADVISOR_PEOPLE_INTEL_MODEL."
        ) from e


@bp.route("/api/v1/people-intel", methods=["POST"])
def people_intel_api():
    """Sub-agent entrypoint: public snippets in → structured people intel out."""
    payload = request.get_json(silent=True) or {}
    person = (payload.get("person") or payload.get("person_name") or "").strip()
    if not person:
        return jsonify(error="person or person_name is required"), 400

    raw_snippets = payload.get("snippets") or payload.get("public_source_snippets")
    if not isinstance(raw_snippets, list):
        return jsonify(error="snippets (array) or public_source_snippets (array) is required"), 400

    snippets: list[dict[str, str]] = []
    for item in raw_snippets:
        if isinstance(item, dict):
            snippets.append(
                {
                    "source_label": str(item.get("source_label") or item.get("source") or ""),
                    "content": str(item.get("content") or item.get("text") or ""),
                }
            )

    company = payload.get("company")
    company_s = str(company).strip() if company else None
    notes = payload.get("notes") or payload.get("extra_notes")
    notes_s = str(notes).strip() if notes else None

    try:
        result = analyze_public_professional_context(
            person=person,
            company=company_s,
            snippets=snippets,
            extra_notes=notes_s,
        )
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except RuntimeError as e:
        return jsonify(error=str(e)), 503
    except Exception as e:
        return jsonify(error="Unexpected error during people-intel workflow.", detail=str(e)), 500

    return jsonify(result)


@bp.route("/api/v1/people-intel/schema", methods=["GET"])
def people_intel_schema():
    """Describe request/response shape for orchestrators calling this sub-agent."""
    return jsonify(
        {
            "description": "Public professional context synthesis; not psychological profiling.",
            "post": "/api/v1/people-intel",
            "request": {
                "person": "string (required)",
                "company": "string (optional)",
                "snippets": [
                    {
                        "source_label": "e.g. LinkedIn, company team page, conference talk",
                        "content": "verbatim or pasted public text the caller obtained legally",
                    }
                ],
                "notes": "optional string — orchestrator context, still subject to safety rules",
            },
            "response": {
                "person": "string",
                "likely_role": "string",
                "confidence": "number 0-1",
                "sources": "string[]",
                "professional_interests": "string[]",
                "communication_style_signals": "string[] — public/professional tone signals only",
                "stakeholder_likelihood": {
                    "decision_maker": "number 0-1",
                    "recruiter": "number 0-1",
                    "hiring_manager": "number 0-1",
                },
                "professional_summary": "string",
                "safe_outreach_angle": "string",
                "limitations": "optional string",
            },
        }
    )
