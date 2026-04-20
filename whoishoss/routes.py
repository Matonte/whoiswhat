"""HTTP routes for the WhoIsHoss microservice."""

import json

from flask import Blueprint, jsonify, render_template_string, request
from sqlalchemy import text

from .extensions import db
from .models import HossConfig, HossProfile, HossQuestion, HossRun, HossTrainingSample

bp = Blueprint("hoss", __name__)


_HOME_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WhoIsHoss</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 42rem; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }
    h1 { font-size: 1.5rem; }
    code { font-size: 0.9em; background: #f4f4f5; padding: 0.1em 0.35em; border-radius: 4px; }
    a { color: #2563eb; }
    ul { padding-left: 1.2rem; }
    .muted { color: #64748b; font-size: 0.9rem; }
    .tag { display: inline-block; font-size: 0.75rem; padding: 0.1rem 0.5rem; border-radius: 999px; background: #fef3c7; color: #92400e; margin-left: 0.5rem; }
  </style>
</head>
<body>
  <h1>WhoIsHoss <span class="tag">microservice</span></h1>
  <p class="muted">Sibling service to WhoIsWhat. Classifies fictional characters / invented personas along the HOSS F-scale archetype.</p>
  <ul>
    <li><a href="/hoss"><strong>Classifier UI</strong></a> — name + optional notes → HOSS level + rationale</li>
    <li><a href="/api/v1/hoss/labels">GET /api/v1/hoss/labels</a> — thresholds, weights, item mapping</li>
    <li><a href="/api/v1/hoss/questions">GET /api/v1/hoss/questions</a> — 30-item F-scale bank</li>
    <li><a href="/api/v1/hoss/training-examples">GET /api/v1/hoss/training-examples</a></li>
    <li><a href="/api/v1/hoss/profiles">GET /api/v1/hoss/profiles</a> — stored classifications</li>
    <li><a href="/health">GET /health</a></li>
  </ul>
  <p class="muted">Output is a stylized fictional/archetypal classification, not a diagnosis. Real private individuals are out of scope by design.</p>
</body>
</html>
"""


_CLASSIFY_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WhoIsHoss — Classify</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 52rem; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }
    h1 { font-size: 1.35rem; }
    h2 { font-size: 0.95rem; margin: 0 0 0.5rem 0; color: #334155; text-transform: uppercase; letter-spacing: 0.04em; }
    label { display: block; font-weight: 600; margin-top: 1rem; margin-bottom: 0.35rem; }
    input[type="text"], textarea { width: 100%; box-sizing: border-box; padding: 0.5rem 0.65rem; font: inherit; border: 1px solid #ccc; border-radius: 6px; }
    textarea { min-height: 5rem; font-family: inherit; }
    button { margin-top: 1rem; padding: 0.55rem 1.2rem; font: inherit; background: #b91c1c; color: #fff; border: none; border-radius: 6px; cursor: pointer; }
    button:disabled { opacity: 0.55; cursor: not-allowed; }
    .section-out { margin-top: 1.75rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; }
    .section-out h2.section-title { font-size: 1rem; margin: 0 0 0.75rem 0; color: #0f172a; text-transform: none; letter-spacing: normal; }
    .outputs { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; align-items: stretch; }
    @media (max-width: 640px) { .outputs { grid-template-columns: 1fr; } }
    .out-panel {
      padding: 1rem 1.1rem; background: #fff7ed; border: 1px solid #fed7aa; border-radius: 10px;
      min-height: 8rem; white-space: pre-wrap; word-break: break-word;
    }
    .out-panel .label-big { font-size: 1.5rem; font-weight: 700; color: #0f172a; letter-spacing: 0.02em; }
    .out-panel .label-sub { font-size: 0.9rem; margin-top: 0.35rem; color: #475569; }
    .out-panel .score-line { margin-top: 0.85rem; font-size: 0.92rem; color: #1e293b; font-weight: 600; }
    .out-panel .traits { margin-top: 0.5rem; font-size: 0.85rem; color: #475569; }
    #out-explain { font-size: 0.98rem; color: #1e293b; line-height: 1.55; background: #f8fafc; border-color: #e2e8f0; }
    #err { margin-top: 1rem; padding: 0.75rem 1rem; border-radius: 8px; display: none; background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; white-space: pre-wrap; word-break: break-word; }
    #err.show { display: block; }
    .muted { color: #64748b; font-size: 0.9rem; }
    a { color: #2563eb; }
  </style>
</head>
<body>
  <p><a href="/">← Home</a></p>
  <h1>HOSS classification</h1>
  <p class="muted">Enter a fictional character or invented persona. Optional notes help ground the result.</p>
  <form id="f">
    <label for="subject_name">Subject name</label>
    <input type="text" id="subject_name" name="subject_name" placeholder="e.g. Walter White" required autocomplete="off">
    <label for="subject_source">Source / context (optional)</label>
    <input type="text" id="subject_source" name="subject_source" placeholder="e.g. Breaking Bad, invented, self-report" autocomplete="off">
    <label for="subject_notes">Notes (optional)</label>
    <textarea id="subject_notes" name="subject_notes" placeholder="Optional behavioral notes to ground the classification."></textarea>
    <button type="submit" id="go">Classify</button>
  </form>
  <div id="err" role="alert"></div>
  <div class="section-out">
    <h2 class="section-title">Results</h2>
    <div class="outputs" aria-live="polite">
      <section>
        <h2>HOSS level</h2>
        <div id="out-level" class="out-panel">Submit to see the HOSS level, label, and traits here.</div>
      </section>
      <section>
        <h2>Explanation</h2>
        <div id="out-explain" class="out-panel">Model rationale will appear here.</div>
      </section>
    </div>
  </div>
  <script>
  function clearErr() {
    const e = document.getElementById("err");
    e.textContent = "";
    e.classList.remove("show");
  }
  function showErr(msg) {
    const e = document.getElementById("err");
    e.textContent = msg;
    e.classList.add("show");
  }
  document.getElementById("f").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const outL = document.getElementById("out-level");
    const outE = document.getElementById("out-explain");
    const btn = document.getElementById("go");
    const name = document.getElementById("subject_name").value.trim();
    const source = document.getElementById("subject_source").value.trim();
    const notes = document.getElementById("subject_notes").value.trim();
    clearErr();
    if (!name) {
      showErr("Please enter a subject name.");
      return;
    }
    btn.disabled = true;
    outL.innerHTML = '<span class="muted">Calling the model…</span>';
    outE.textContent = "";
    try {
      const r = await fetch("/api/v1/hoss/classify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name, source: source || null, input_summary: notes || null })
      });
      const data = await r.json();
      if (!r.ok) {
        outL.textContent = "—";
        outE.textContent = "";
        const parts = [data.error || ("HTTP " + r.status)];
        if (data.detail) parts.push(data.detail);
        showErr(parts.join("\\n\\n"));
        return;
      }
      const label = data.display_label || "(missing)";
      const internal = data.internal_label || "";
      const level = data.hoss_level;
      const score = data.hoss_score;
      const t = data.traits || {};
      outL.innerHTML =
        '<div class="label-big">' + escapeHtml(label) + '</div>' +
        '<div class="label-sub">level ' + escapeHtml(String(level)) + ' · ' + escapeHtml(internal) + '</div>' +
        '<div class="score-line">HOSS score: <strong>' + escapeHtml(String(score)) + '</strong> / 5.0</div>' +
        '<div class="traits">square <strong>' + escapeHtml(String(t.square)) + '</strong> · ' +
        'punisher <strong>' + escapeHtml(String(t.punisher)) + '</strong> · ' +
        'power <strong>' + escapeHtml(String(t.power)) + '</strong> · ' +
        'skull <strong>' + escapeHtml(String(t.skull)) + '</strong></div>';
      outE.textContent = data.explanation || data.short_explanation || "(No rationale returned.)";
    } catch (err) {
      outL.textContent = "—";
      outE.textContent = "";
      showErr("Network or browser error: " + err);
    } finally {
      btn.disabled = false;
    }
  });
  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }
  </script>
</body>
</html>
"""


@bp.route("/")
def home():
    return render_template_string(_HOME_HTML)


@bp.route("/hoss")
def hoss_ui():
    return render_template_string(_CLASSIFY_HTML)


@bp.route("/api/v1/hoss/labels")
def hoss_labels():
    row = HossConfig.query.filter_by(name="hoss_labels").one_or_none()
    if row is None:
        return jsonify(error="hoss_labels not loaded"), 404
    return jsonify(json.loads(row.document_json))


@bp.route("/api/v1/hoss/questions")
def hoss_questions():
    rows = HossQuestion.query.order_by(HossQuestion.id).all()
    return jsonify([r.to_dict() for r in rows])


@bp.route("/api/v1/hoss/training-examples")
def hoss_training_examples():
    limit = request.args.get("limit", default=500, type=int)
    limit = max(1, min(limit, 2000))
    rows = (
        HossTrainingSample.query.order_by(HossTrainingSample.id).limit(limit).all()
    )
    return jsonify([r.to_dict() for r in rows])


@bp.route("/api/v1/hoss/profiles")
def hoss_profiles_list():
    limit = request.args.get("limit", default=100, type=int)
    limit = max(1, min(limit, 1000))
    rows = (
        HossProfile.query.order_by(HossProfile.created_at.desc()).limit(limit).all()
    )
    return jsonify(
        [
            {
                "id": p.id,
                "name": p.name,
                "source": p.source,
                "hoss_score": p.hoss_score,
                "hoss_level": p.hoss_level,
                "display_label": p.display_label,
                "internal_label": p.internal_label,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in rows
        ]
    )


@bp.route("/api/v1/hoss/profiles/<int:profile_id>")
def hoss_profile_detail(profile_id: int):
    p = HossProfile.query.get_or_404(profile_id)
    return jsonify(
        {
            "id": p.id,
            "name": p.name,
            "source": p.source,
            "input_summary": p.input_summary,
            "f_scale_items": json.loads(p.f_scale_items_json),
            "traits": {
                "square": p.square,
                "punisher": p.punisher,
                "power": p.power,
                "skull": p.skull,
            },
            "hoss_score": p.hoss_score,
            "hoss_level": p.hoss_level,
            "display_label": p.display_label,
            "internal_label": p.internal_label,
            "explanation": p.explanation,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
    )


@bp.route("/api/v1/hoss/classify", methods=["POST"])
def hoss_classify_api():
    """Classify a subject via OpenAI, score deterministically, persist result."""
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    source = (payload.get("source") or "").strip() or "invented"
    input_summary = (payload.get("input_summary") or "").strip() or None

    if not name:
        return jsonify(error="name is required"), 400

    try:
        from .llm import classify_hoss, explain_hoss
        from .scoring import score_from_items

        llm_result = classify_hoss(name, source, input_summary)
        items = llm_result.get("f_scale_items") or {}
        if not items:
            return (
                jsonify(error="Model did not return f_scale_items.", detail=json.dumps(llm_result)),
                502,
            )

        scored = score_from_items(items)

        resolved_source = (llm_result.get("source") or source or "invented").strip()
        resolved_summary = (
            llm_result.get("input_summary") or input_summary or ""
        ).strip() or None

        short_explanation = (llm_result.get("short_explanation") or "").strip() or None
        explanation = explain_hoss(
            name=name,
            source=resolved_source,
            traits=scored["traits"],
            hoss_score=scored["hoss_score"],
            display_label=scored["display_label"],
            short_explanation=short_explanation,
        )

        result: dict = {
            "name": name,
            "source": resolved_source,
            "input_summary": resolved_summary,
            "f_scale_items": scored["f_scale_items"],
            "traits": scored["traits"],
            "hoss_score": scored["hoss_score"],
            "hoss_level": scored["hoss_level"],
            "display_label": scored["display_label"],
            "internal_label": scored["internal_label"],
            "explanation": explanation,
        }

        profile = HossProfile(
            name=name,
            source=resolved_source,
            input_summary=resolved_summary,
            f_scale_items_json=json.dumps(scored["f_scale_items"], ensure_ascii=False),
            square=scored["traits"]["square"],
            punisher=scored["traits"]["punisher"],
            power=scored["traits"]["power"],
            skull=scored["traits"]["skull"],
            hoss_score=scored["hoss_score"],
            hoss_level=scored["hoss_level"],
            display_label=scored["display_label"],
            internal_label=scored["internal_label"],
            explanation=explanation,
        )
        db.session.add(profile)
        db.session.add(
            HossRun(
                profile_name=name,
                profile_source=resolved_source,
                request_payload_json=json.dumps(payload, ensure_ascii=False),
                response_payload_json=json.dumps(result, ensure_ascii=False),
            )
        )
        db.session.commit()
        result["id"] = profile.id

    except RuntimeError as e:
        return jsonify(error=str(e)), 503
    except Exception as e:
        return jsonify(error="Unexpected error during HOSS classification.", detail=str(e)), 500

    return jsonify(result)


@bp.route("/health")
def health():
    db.session.execute(text("SELECT 1"))
    return jsonify(status="ok", service="whoishoss", database="connected")
