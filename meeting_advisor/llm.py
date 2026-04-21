"""LLM integration for meeting advice.

Takes the merged K + HOSS profile plus a user-supplied context and asks
the model for a strictly-typed JSON recommendation.
"""

from __future__ import annotations

import json
import os
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, OpenAIError


SYSTEM_PROMPT = """You are a meeting-preparation advisor. You are NOT a therapist, profiler, or diagnostician.

You will receive JSON in the user message containing:
- subject_name: string
- k_profile: the structured output from the WhoIsWhat K-taxonomy classifier (may be null on error)
- hoss_profile: the structured output from the WhoIsHoss HOSS F-scale classifier (may be null on error)
- context: the user's planned meeting context (setting, your_role, stakes, goals, optional notes)

Rules:
- Stay grounded in the two profiles + the supplied context. Do not invent facts about the subject beyond what the profiles say.
- Treat profiles as stylized/archetypal signals, not psychological diagnoses.
- Prefer concrete, specific tactical guidance over platitudes.
- Calibrate uncertainty: if profiles are thin, missing, or contradictory, say so in key_observations and reduce risk_level accordingly.
- Refuse to produce guidance that is manipulative, coercive, illegal, or designed to harm the subject. If the user's goals appear to require that, reflect the refusal inside key_observations and escalation_plan and still return valid JSON.
- Never reveal or quote the raw profile JSON back to the user.

Return a single JSON object and no other text. Required keys:
- "risk_level": one of "low", "medium", "high"
- "key_observations": string (3-5 sentences summarizing what the profiles + context imply for THIS meeting)
- "do": array of 3-6 short imperative strings
- "dont": array of 3-6 short imperative strings
- "opening_move": string (1-2 sentences — concrete suggested opening for this meeting)
- "watchpoints": array of 2-5 short strings describing signals to watch for during the meeting
- "escalation_plan": string (what to do if the meeting starts going sideways)
"""


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


def advise(
    subject_name: str,
    k_profile: dict[str, Any] | None,
    hoss_profile: dict[str, Any] | None,
    context: dict[str, Any],
    *,
    model: str | None = None,
) -> tuple[dict[str, Any], str]:
    """Return (advice_dict, model_used). Raises RuntimeError with a human-readable message on failure."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or not api_key.strip():
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")

    if k_profile is None and hoss_profile is None:
        raise RuntimeError(
            "Neither WhoIsWhat nor WhoIsHoss returned a profile. Cannot produce advice."
        )

    model = (
        model
        or os.environ.get("ADVISOR_MODEL")
        or os.environ.get("OPENAI_MODEL")
        or "gpt-5.4"
    )

    user_payload = {
        "subject_name": subject_name,
        "k_profile": k_profile,
        "hoss_profile": hoss_profile,
        "context": context,
    }

    client = OpenAI(api_key=api_key)
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
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
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "The model did not return valid JSON. Try again or set OPENAI_MODEL to another model."
        ) from e

    return parsed, model
