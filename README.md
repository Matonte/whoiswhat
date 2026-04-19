# WhoIsWhat

Flask + SQLAlchemy app that loads a **K taxonomy** (categories + dimensions + edges) and **behavior-classification training examples** from `data/raw/`, stores them in a relational schema, and exposes them over JSON APIs for evaluation and training workflows.

## Requirements

- Python 3.12+ (see `requirements.txt`)
- A virtual environment (recommended)

## Setup

From the project root:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set `DATABASE_URL` (SQLite or PostgreSQL). For SQLite, prefer running commands from the project root with e.g. `DATABASE_URL=sqlite:///./whoiswhat.db`.

## Dataset files (`data/raw/`)

Canonical imports (used by the loader):

| File | Role |
|------|------|
| `k_training_schema.json` | Evaluation criteria: task type, label space, dimension definitions, field list |
| `k_taxonomy_graph.json` | Taxonomy **nodes** and **edges** (same graph as CSV bundle) |
| `k_training_examples.jsonl` | Training rows (one JSON object per line) |
| `k_training_examples.csv` | Same examples in CSV form; merged with JSONL by `example_id` |

Also present for reference / tooling (not required for DB import):

- `k_taxonomy_nodes.csv`, `k_taxonomy_edges.csv` — same graph as `k_taxonomy_graph.json`
- `k_taxonomy.graphml` — same graph in GraphML
- `*_preview.csv` — small previews

To refresh files from another machine, copy them into `data/raw/` and run:

```powershell
flask --app wsgi import-k-data --force
```

(`wsgi.py` instantiates the app so Flask CLI commands are available.)

## Run (development)

```powershell
python run.py
```

On first startup this creates tables and, if the taxonomy is empty, imports from `data/raw/`.

## HTTP API

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/evaluation-criteria` | Parsed `k_training_schema.json` (dataset name, label space, dimensions, fields) |
| `GET /api/v1/taxonomy/graph` | Full `k_taxonomy_graph.json` snapshot |
| `GET /api/v1/taxonomy/nodes` | All taxonomy nodes |
| `GET /api/v1/taxonomy/edges` | All taxonomy edges |
| `GET /api/v1/training-examples?limit=500` | Labeled training examples (default limit 500, max 2000) |
| `GET /health` | DB connectivity |
| `GET /classify` | **Web UI** — enter a subject name only; two read-only panels show K grouping and reasoning |
| `POST /api/v1/classify` | JSON body `{"subject_name":"..."}` (optional `"character"` for API clients) → structured classification |

### ChatGPT / OpenAI

The classifier sends your **stored evaluation criteria** (`k_training_schema`) and **training examples** from the database in the **system** prompt, then asks the model to assign a `classification_code` / `classification_label`, three 0–5 scores, and a `short_rationale`.

1. Add to `.env`: `OPENAI_API_KEY=sk-...` (see `.env.example`).
2. Optionally set `OPENAI_MODEL` (default `gpt-4o-mini`).
3. Ensure data is imported (`python run.py` once or `flask --app wsgi import-k-data`).
4. Open **http://127.0.0.1:5000/classify** and submit the form.

The API never sends your API key to the browser; only the Flask server calls OpenAI.

## Project layout

```
.
├── README.md
├── requirements.txt
├── run.py
├── wsgi.py
├── data/
│   └── raw/                 # K taxonomy + training source files
├── whoiswhat/
│   ├── __init__.py          # create_app(), Flask CLI
│   ├── extensions.py
│   ├── models.py            # DatasetSchema, TaxonomyNode, TaxonomyEdge, TrainingExample
│   ├── importer.py          # load JSON/JSONL/CSV into DB
│   ├── llm.py               # OpenAI classification using DB criteria + examples
│   └── routes.py
├── .env.example
└── .env
```

## Database schema (summary)

- **`dataset_schemas`** — JSON documents: evaluation spec (`dataset_name` = `k_taxonomy_training_examples`) and full graph snapshot (`k_taxonomy_graph`).
- **`taxonomy_nodes`** — `node_id`, `node_type`, `label`, `description`.
- **`taxonomy_edges`** — `source_node_id`, `target_node_id`, `relation`.
- **`training_examples`** — columns aligned with `k_training_schema.json` `fields`.

## Optional next steps

- Flask-Migrate (Alembic) for schema evolution  
- GraphML parser if you want first-class imports from `.graphml` only  
- Tests (`pytest`) and auth for non-public deployments  
