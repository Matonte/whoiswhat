"""HTTP routes for the meeting_advisor service."""

import json

from flask import Blueprint, current_app, jsonify, render_template_string, request
from sqlalchemy import text

from .clients import cache_lookup, cache_upsert, classify_hoss, classify_k
from .extensions import db
from .llm import advise
from .models import AdviceRun

bp = Blueprint("advisor", __name__)


SETTING_OPTIONS = [
    "work", "social", "family", "negotiation", "first-date", "conflict", "interview", "other",
]
STAKES_OPTIONS = ["low", "medium", "high"]


_HOME_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Meeting Advisor</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 44rem; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }
    h1 { font-size: 1.5rem; }
    a { color: #2563eb; }
    ul { padding-left: 1.2rem; }
    .muted { color: #64748b; font-size: 0.9rem; }
    .tag { display: inline-block; font-size: 0.75rem; padding: 0.1rem 0.5rem; border-radius: 999px; background: #dcfce7; color: #166534; margin-left: 0.5rem; }
  </style>
</head>
<body>
  <h1>Meeting Advisor <span class="tag">aggregator</span></h1>
  <p class="muted">Calls WhoIsWhat + WhoIsHoss over HTTP, merges both profiles with your meeting context, and returns tactical guidance.</p>
  <ul>
    <li><a href="/advise"><strong>Advisor UI</strong></a> — subject name + notes + meeting context → guidance</li>
    <li><a href="/api/v1/advice">GET /api/v1/advice</a> — list past advice runs</li>
    <li><a href="/health">GET /health</a></li>
  </ul>
  <p class="muted">Output is stylized/archetypal; not a diagnosis or psychological assessment.</p>
</body>
</html>
"""


_ADVISE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Meeting Advisor — Plan a meeting</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 56rem; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }
    h1 { font-size: 1.35rem; }
    h2 { font-size: 0.95rem; margin: 0 0 0.5rem 0; color: #334155; text-transform: uppercase; letter-spacing: 0.04em; }
    label { display: block; font-weight: 600; margin-top: 0.8rem; margin-bottom: 0.35rem; }
    input[type="text"], select, textarea { width: 100%; box-sizing: border-box; padding: 0.5rem 0.65rem; font: inherit; border: 1px solid #ccc; border-radius: 6px; }
    textarea { min-height: 4.5rem; font-family: inherit; }
    .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    @media (max-width: 640px) { .grid2 { grid-template-columns: 1fr; } }
    button { margin-top: 1rem; padding: 0.55rem 1.2rem; font: inherit; background: #16a34a; color: #fff; border: none; border-radius: 6px; cursor: pointer; }
    button:disabled { opacity: 0.55; cursor: not-allowed; }
    .section-out { margin-top: 1.75rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; }
    .outputs { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; align-items: stretch; }
    @media (max-width: 860px) { .outputs { grid-template-columns: 1fr; } }
    .out-panel { padding: 1rem 1.1rem; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; min-height: 8rem; }
    .risk-badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 999px; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; }
    .risk-low { background: #dcfce7; color: #166534; }
    .risk-medium { background: #fef3c7; color: #92400e; }
    .risk-high { background: #fee2e2; color: #991b1b; }
    .profile { font-size: 0.9rem; color: #1e293b; white-space: pre-wrap; word-break: break-word; }
    .list-compact { margin: 0.35rem 0 0.75rem 1.1rem; padding: 0; }
    .list-compact li { margin-bottom: 0.25rem; }
    #err { margin-top: 1rem; padding: 0.75rem 1rem; border-radius: 8px; display: none; background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; white-space: pre-wrap; word-break: break-word; }
    #err.show { display: block; }
    .muted { color: #64748b; font-size: 0.9rem; }
    a { color: #2563eb; }
    .kv { font-size: 0.92rem; }
    .kv strong { color: #0f172a; }
  </style>
</head>
<body>
  <p><a href="/">← Home</a></p>
  <h1>Plan a meeting</h1>
  <p class="muted">Enter the subject + your meeting context. The advisor calls WhoIsWhat and WhoIsHoss over HTTP, merges both profiles, and returns tactical guidance.</p>
  <form id="f">
    <div class="grid2">
      <div>
        <label for="subject_name">Subject name</label>
        <input type="text" id="subject_name" required autocomplete="off" placeholder="e.g. Walter White">
      </div>
      <div>
        <label for="source_hint">Source / context hint (optional)</label>
        <input type="text" id="source_hint" autocomplete="off" placeholder="e.g. Breaking Bad, work colleague, invented">
      </div>
    </div>
    <label for="notes">Notes about the subject (optional)</label>
    <textarea id="notes" placeholder="Optional behavior notes to ground both classifiers."></textarea>

    <h2 style="margin-top: 1.25rem;">Meeting context</h2>
    <div class="grid2">
      <div>
        <label for="setting">Setting</label>
        <select id="setting">__SETTING_OPTIONS__</select>
      </div>
      <div>
        <label for="stakes">Stakes</label>
        <select id="stakes">__STAKES_OPTIONS__</select>
      </div>
    </div>
    <label for="your_role">Your role</label>
    <input type="text" id="your_role" placeholder="e.g. project manager, ex-colleague, prospective buyer">
    <label for="goals">Your goals for the meeting</label>
    <textarea id="goals" placeholder="What do you want out of the meeting?"></textarea>

    <button type="submit" id="go">Get meeting advice</button>
  </form>
  <div id="err" role="alert"></div>

  <div class="section-out">
    <h2>Profiles</h2>
    <div class="outputs">
      <section>
        <h2>K taxonomy (WhoIsWhat)</h2>
        <div id="out-k" class="out-panel profile">Submit to see the K classification.</div>
      </section>
      <section>
        <h2>HOSS (WhoIsHoss)</h2>
        <div id="out-hoss" class="out-panel profile">Submit to see the HOSS classification.</div>
      </section>
    </div>
  </div>

  <div class="section-out">
    <h2>Meeting guidance</h2>
    <div id="advice" class="out-panel profile">Guidance will appear here.</div>
  </div>

  <script>
  function clearErr() { const e = document.getElementById("err"); e.textContent = ""; e.classList.remove("show"); }
  function showErr(msg) { const e = document.getElementById("err"); e.textContent = msg; e.classList.add("show"); }
  function esc(s) { const d = document.createElement("div"); d.textContent = s == null ? "" : String(s); return d.innerHTML; }
  function list(items) {
    if (!items || !items.length) return "<em class='muted'>(none)</em>";
    return "<ul class='list-compact'>" + items.map(i => "<li>" + esc(i) + "</li>").join("") + "</ul>";
  }

  document.getElementById("f").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const btn = document.getElementById("go");
    const outK = document.getElementById("out-k");
    const outH = document.getElementById("out-hoss");
    const outA = document.getElementById("advice");
    clearErr();
    const payload = {
      subject_name: document.getElementById("subject_name").value.trim(),
      source_hint: document.getElementById("source_hint").value.trim() || null,
      notes: document.getElementById("notes").value.trim() || null,
      context: {
        setting: document.getElementById("setting").value,
        stakes: document.getElementById("stakes").value,
        your_role: document.getElementById("your_role").value.trim() || null,
        goals: document.getElementById("goals").value.trim() || null
      }
    };
    if (!payload.subject_name) { showErr("Please enter a subject name."); return; }
    btn.disabled = true;
    outK.innerHTML = "<span class='muted'>Calling WhoIsWhat…</span>";
    outH.innerHTML = "<span class='muted'>Calling WhoIsHoss…</span>";
    outA.innerHTML = "<span class='muted'>Generating meeting guidance…</span>";
    try {
      const r = await fetch("/api/v1/advise", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await r.json();
      if (!r.ok) {
        outK.textContent = "—"; outH.textContent = "—"; outA.textContent = "";
        const parts = [data.error || ("HTTP " + r.status)];
        if (data.detail) parts.push(data.detail);
        showErr(parts.join("\\n\\n"));
        return;
      }
      // K panel
      const k = data.k_profile;
      if (data.k_error) {
        outK.innerHTML = "<span class='muted'>K classifier failed:</span><br>" + esc(data.k_error);
      } else if (k) {
        outK.innerHTML =
          "<div class='kv'><strong>" + esc(k.classification_code || "?") + "</strong> — " + esc(k.classification_label || "") + "</div>" +
          "<div class='kv muted'>awareness " + esc(k.awareness_failure_score) + " · intent " + esc(k.intent_failure_score) + " · control " + esc(k.control_failure_score) + "</div>" +
          "<div style='margin-top:0.5rem'>" + esc(k.short_rationale || "") + "</div>";
      } else { outK.textContent = "—"; }
      // HOSS panel
      const h = data.hoss_profile;
      if (data.hoss_error) {
        outH.innerHTML = "<span class='muted'>HOSS classifier failed:</span><br>" + esc(data.hoss_error);
      } else if (h) {
        const t = h.traits || {};
        outH.innerHTML =
          "<div class='kv'><strong>" + esc(h.display_label || "") + "</strong> · level " + esc(h.hoss_level) + " (" + esc(h.internal_label) + ")" + (h._reused ? " <span class='muted'>· reused</span>" : "") + "</div>" +
          "<div class='kv muted'>hoss_score " + esc(h.hoss_score) + " · sq " + esc(t.square) + " · pu " + esc(t.punisher) + " · po " + esc(t.power) + " · sk " + esc(t.skull) + "</div>" +
          "<div style='margin-top:0.5rem'>" + esc(h.explanation || "") + "</div>";
      } else { outH.textContent = "—"; }
      // Advice panel
      const a = data.advice || {};
      const rl = (a.risk_level || "").toLowerCase();
      const badgeClass = rl === "high" ? "risk-high" : rl === "medium" ? "risk-medium" : rl ? "risk-low" : "";
      outA.innerHTML =
        (rl ? "<span class='risk-badge " + badgeClass + "'>" + esc(rl) + " risk</span>" : "") +
        "<div style='margin-top:0.6rem'>" + esc(a.key_observations || "") + "</div>" +
        "<h3 style='margin-top:0.9rem; margin-bottom:0.2rem; font-size:0.95rem;'>Do</h3>" + list(a.do) +
        "<h3 style='margin-top:0.4rem; margin-bottom:0.2rem; font-size:0.95rem;'>Don't</h3>" + list(a.dont) +
        "<h3 style='margin-top:0.4rem; margin-bottom:0.2rem; font-size:0.95rem;'>Opening move</h3><div>" + esc(a.opening_move || "") + "</div>" +
        "<h3 style='margin-top:0.4rem; margin-bottom:0.2rem; font-size:0.95rem;'>Watch for</h3>" + list(a.watchpoints) +
        "<h3 style='margin-top:0.4rem; margin-bottom:0.2rem; font-size:0.95rem;'>If things go sideways</h3><div>" + esc(a.escalation_plan || "") + "</div>";
    } catch (err) {
      outK.textContent = "—"; outH.textContent = "—"; outA.textContent = "";
      showErr("Network or browser error: " + err);
    } finally {
      btn.disabled = false;
    }
  });
  </script>
</body>
</html>
"""


def _render_advise_html() -> str:
    setting_html = "".join(f'<option value="{o}">{o}</option>' for o in SETTING_OPTIONS)
    stakes_html = "".join(f'<option value="{o}">{o}</option>' for o in STAKES_OPTIONS)
    return _ADVISE_HTML.replace("__SETTING_OPTIONS__", setting_html).replace(
        "__STAKES_OPTIONS__", stakes_html
    )


@bp.route("/")
def home():
    return render_template_string(_HOME_HTML)


@bp.route("/advise")
def advise_ui():
    return render_template_string(_render_advise_html())


@bp.route("/health")
def health():
    db.session.execute(text("SELECT 1"))
    return jsonify(
        status="ok",
        service="meeting_advisor",
        whoiswhat_url=current_app.config["WHOISWHAT_URL"],
        whoishoss_url=current_app.config["WHOISHOSS_URL"],
        database="connected",
    )


@bp.route("/api/v1/advice")
def list_advice():
    limit = request.args.get("limit", default=50, type=int)
    limit = max(1, min(limit, 500))
    rows = AdviceRun.query.order_by(AdviceRun.created_at.desc()).limit(limit).all()
    return jsonify(
        [
            {
                "id": r.id,
                "subject_name": r.subject_name,
                "source_hint": r.source_hint,
                "risk_level": r.risk_level,
                "model": r.model,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    )


@bp.route("/api/v1/advice/<int:run_id>")
def get_advice(run_id: int):
    r = AdviceRun.query.get_or_404(run_id)
    return jsonify(
        {
            "id": r.id,
            "subject_name": r.subject_name,
            "source_hint": r.source_hint,
            "context": json.loads(r.context_json),
            "k_profile": json.loads(r.k_profile_json) if r.k_profile_json else None,
            "hoss_profile": (
                json.loads(r.hoss_profile_json) if r.hoss_profile_json else None
            ),
            "advice": json.loads(r.advice_json),
            "risk_level": r.risk_level,
            "model": r.model,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
    )


@bp.route("/api/v1/advise", methods=["POST"])
def advise_api():
    payload = request.get_json(silent=True) or {}
    subject_name = (payload.get("subject_name") or "").strip()
    if not subject_name:
        return jsonify(error="subject_name is required"), 400

    source_hint = (payload.get("source_hint") or "").strip()
    notes = (payload.get("notes") or "").strip() or None
    context = payload.get("context") or {}
    if not isinstance(context, dict):
        return jsonify(error="context must be an object"), 400

    # 1. Cache lookup
    cached = cache_lookup(subject_name, source_hint)
    if cached is not None:
        k_profile = json.loads(cached.k_profile_json) if cached.k_profile_json else None
        hoss_profile = (
            json.loads(cached.hoss_profile_json) if cached.hoss_profile_json else None
        )
        k_error = None
        hoss_error = None
        if hoss_profile is not None:
            hoss_profile["_reused"] = True
    else:
        # 2. Fan out over HTTP
        k_profile, k_error = classify_k(subject_name, notes=notes)
        hoss_profile, hoss_error = classify_hoss(
            subject_name, source_hint=source_hint or None, notes=notes
        )
        if k_profile is not None or hoss_profile is not None:
            cache_upsert(subject_name, source_hint, k_profile, hoss_profile)

    # 3. Call LLM advisor
    try:
        advice_json, model_used = advise(
            subject_name=subject_name,
            k_profile=k_profile,
            hoss_profile=hoss_profile,
            context=context,
        )
    except RuntimeError as e:
        return (
            jsonify(
                error=str(e),
                k_profile=k_profile,
                k_error=k_error,
                hoss_profile=hoss_profile,
                hoss_error=hoss_error,
            ),
            503,
        )
    except Exception as e:
        return (
            jsonify(error="Unexpected error producing advice.", detail=str(e)),
            500,
        )

    # 4. Persist advice_runs
    risk_level = (advice_json.get("risk_level") or "").strip().lower() or None
    run = AdviceRun(
        subject_name=subject_name,
        source_hint=source_hint or None,
        context_json=json.dumps(context, ensure_ascii=False),
        k_profile_json=json.dumps(k_profile, ensure_ascii=False) if k_profile else None,
        hoss_profile_json=(
            json.dumps(hoss_profile, ensure_ascii=False) if hoss_profile else None
        ),
        advice_json=json.dumps(advice_json, ensure_ascii=False),
        risk_level=risk_level,
        model=model_used,
    )
    db.session.add(run)
    db.session.commit()

    return jsonify(
        id=run.id,
        subject_name=subject_name,
        source_hint=source_hint or None,
        context=context,
        k_profile=k_profile,
        k_error=k_error,
        hoss_profile=hoss_profile,
        hoss_error=hoss_error,
        advice=advice_json,
        risk_level=risk_level,
        model=model_used,
    )
