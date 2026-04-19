import json

from flask import Blueprint, jsonify, render_template_string, request
from sqlalchemy import text

from .extensions import db
from .models import DatasetSchema, TaxonomyEdge, TaxonomyNode, TrainingExample

bp = Blueprint("main", __name__)


_HOME_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WhoIsWhat</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 42rem; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }
    h1 { font-size: 1.5rem; }
    code { font-size: 0.9em; background: #f4f4f5; padding: 0.1em 0.35em; border-radius: 4px; }
    a { color: #2563eb; }
    ul { padding-left: 1.2rem; }
    .muted { color: #64748b; font-size: 0.9rem; }
  </style>
</head>
<body>
  <h1>WhoIsWhat</h1>
  <p class="muted">K taxonomy + training dataset (evaluation criteria and labeled examples).</p>
  <ul>
    <li><a href="/api/v1/evaluation-criteria">GET /api/v1/evaluation-criteria</a> — task schema JSON</li>
    <li><a href="/api/v1/taxonomy/nodes">GET /api/v1/taxonomy/nodes</a></li>
    <li><a href="/api/v1/taxonomy/edges">GET /api/v1/taxonomy/edges</a></li>
    <li><a href="/api/v1/training-examples">GET /api/v1/training-examples</a></li>
    <li><a href="/health">GET /health</a></li>
    <li><a href="/classify"><strong>Classifier UI</strong></a> — name + character → label + reasoning (ChatGPT)</li>
  </ul>
</body>
</html>
"""


_CLASSIFY_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WhoIsWhat — Classify</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 52rem; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }
    h1 { font-size: 1.35rem; }
    h2 { font-size: 0.95rem; margin: 0 0 0.5rem 0; color: #334155; text-transform: uppercase; letter-spacing: 0.04em; }
    label { display: block; font-weight: 600; margin-top: 1rem; margin-bottom: 0.35rem; }
    input[type="text"] { width: 100%; max-width: 28rem; box-sizing: border-box; padding: 0.5rem 0.65rem; font: inherit; border: 1px solid #ccc; border-radius: 6px; }
    button { margin-top: 1rem; padding: 0.55rem 1.2rem; font: inherit; background: #1d4ed8; color: #fff; border: none; border-radius: 6px; cursor: pointer; }
    button:disabled { opacity: 0.55; cursor: not-allowed; }
    .section-out { margin-top: 1.75rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; }
    .section-out h2.section-title { font-size: 1rem; margin: 0 0 0.75rem 0; color: #0f172a; text-transform: none; letter-spacing: normal; }
    .outputs { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; align-items: stretch; }
    @media (max-width: 640px) { .outputs { grid-template-columns: 1fr; } }
    .out-panel {
      padding: 1rem 1.1rem; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;
      min-height: 8rem; white-space: pre-wrap; word-break: break-word;
    }
    .out-panel .k-code { font-size: 1.75rem; font-weight: 700; color: #0f172a; letter-spacing: 0.02em; }
    .out-panel .k-label { font-size: 1.1rem; margin-top: 0.35rem; color: #1e293b; }
    .out-panel .k-scores { margin-top: 0.85rem; font-size: 0.88rem; color: #475569; }
    #out-rationale { font-size: 0.98rem; color: #1e293b; line-height: 1.55; }
    #err { margin-top: 1rem; padding: 0.75rem 1rem; border-radius: 8px; display: none; background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; white-space: pre-wrap; word-break: break-word; }
    #err.show { display: block; }
    .muted { color: #64748b; font-size: 0.9rem; }
    a { color: #2563eb; }
  </style>
</head>
<body>
  <p><a href="/">← Home</a></p>
  <h1>Classify a subject</h1>
  <p class="muted">Enter a <strong>person or subject name</strong> only. The two panels below are <strong>outputs only</strong> (K grouping and reasoning).</p>
  <form id="f">
    <label for="subject_name">Person / subject name</label>
    <input type="text" id="subject_name" name="subject_name" placeholder="e.g. Leslie Knope" required autocomplete="off">
    <button type="submit" id="go">Get classification</button>
  </form>
  <div id="err" role="alert"></div>
  <div class="section-out">
    <h2 class="section-title">Results</h2>
    <div class="outputs" aria-live="polite">
      <section>
        <h2>K grouping</h2>
        <div id="out-k" class="out-panel">Submit to see the predicted K code and label here.</div>
      </section>
      <section>
        <h2>Summary / reasoning</h2>
        <div id="out-rationale" class="out-panel">Model rationale will appear here.</div>
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
    const outK = document.getElementById("out-k");
    const outR = document.getElementById("out-rationale");
    const btn = document.getElementById("go");
    const name = document.getElementById("subject_name").value.trim();
    clearErr();
    if (!name) {
      showErr("Please enter a person or subject name.");
      return;
    }
    btn.disabled = true;
    outK.innerHTML = '<span class="muted">Calling the model…</span>';
    outR.textContent = "";
    try {
      const r = await fetch("/api/v1/classify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subject_name: name })
      });
      const data = await r.json();
      if (!r.ok) {
        outK.textContent = "—";
        outR.textContent = "";
        const parts = [data.error || ("HTTP " + r.status)];
        if (data.detail) parts.push(data.detail);
        showErr(parts.join("\\n\\n"));
        return;
      }
      const code = data.classification_code || "?";
      const label = data.classification_label || "(missing)";
      const a = data.awareness_failure_score;
      const i = data.intent_failure_score;
      const c = data.control_failure_score;
      outK.innerHTML =
        '<div class="k-code">' + escapeHtml(code) + '</div>' +
        '<div class="k-label">' + escapeHtml(label) + '</div>' +
        '<div class="k-scores">Dimension scores (0–5): awareness <strong>' + escapeHtml(String(a)) + '</strong>, intent <strong>' + escapeHtml(String(i)) + '</strong>, control <strong>' + escapeHtml(String(c)) + '</strong></div>';
      outR.textContent = data.short_rationale || "(No rationale returned.)";
    } catch (err) {
      outK.textContent = "—";
      outR.textContent = "";
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


@bp.route("/api/v1/evaluation-criteria")
def evaluation_criteria():
    """Primary evaluation spec: k_training_schema.json content."""
    row = DatasetSchema.query.filter_by(name="k_taxonomy_training_examples").one_or_none()
    if row is None:
        return jsonify(error="schema not loaded"), 404
    return jsonify(json.loads(row.document_json))


@bp.route("/api/v1/taxonomy/graph")
def taxonomy_graph_snapshot():
    """Full bundled graph JSON (nodes, edges, embedded schema) from k_taxonomy_graph.json."""
    row = DatasetSchema.query.filter_by(name="k_taxonomy_graph").one_or_none()
    if row is None:
        return jsonify(error="graph snapshot not loaded"), 404
    return jsonify(json.loads(row.document_json))


@bp.route("/api/v1/taxonomy/nodes")
def taxonomy_nodes():
    rows = TaxonomyNode.query.order_by(TaxonomyNode.node_id).all()
    return jsonify(
        [
            {
                "node_id": r.node_id,
                "node_type": r.node_type,
                "label": r.label,
                "description": r.description,
            }
            for r in rows
        ]
    )


@bp.route("/api/v1/taxonomy/edges")
def taxonomy_edges():
    rows = TaxonomyEdge.query.order_by(TaxonomyEdge.id).all()
    return jsonify(
        [
            {
                "source": e.source_node_id,
                "target": e.target_node_id,
                "relation": e.relation,
            }
            for e in rows
        ]
    )


@bp.route("/api/v1/training-examples")
def training_examples():
    limit = request.args.get("limit", default=500, type=int)
    limit = max(1, min(limit, 2000))
    rows = TrainingExample.query.order_by(TrainingExample.example_id).limit(limit).all()
    return jsonify([r.to_dict() for r in rows])


@bp.route("/classify")
def classify_ui():
    return render_template_string(_CLASSIFY_HTML)


@bp.route("/api/v1/classify", methods=["POST"])
def classify_api():
    """Classify using OpenAI; prompt includes DB criteria + training examples."""
    payload = request.get_json(silent=True) or {}
    subject_name = (payload.get("subject_name") or "").strip()
    character = (payload.get("character") or "").strip() or None
    if not subject_name:
        return jsonify(error="subject_name is required"), 400

    try:
        from .llm import classify_subject

        result = classify_subject(subject_name, character)
    except RuntimeError as e:
        return jsonify(error=str(e)), 503
    except Exception as e:
        return jsonify(error="Unexpected error during classification.", detail=str(e)), 500

    return jsonify(result)


@bp.route("/health")
def health():
    db.session.execute(text("SELECT 1"))
    return jsonify(status="ok", database="connected")
