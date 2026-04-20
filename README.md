# WhoIsWhat — monorepo

Two Flask microservices and (planned) an aggregator, designed as a work-sample
project that classifies subjects along two independent taxonomies:

| Service | Role | Port | DB |
|---|---|---|---|
| [`whoiswhat/`](./whoiswhat) | K-taxonomy classifier (criteria + labeled examples) | **5001** (docker) / 5000 (local) | `whoiswhat.db` |
| [`whoishoss/`](./whoishoss) | HOSS F-scale archetype classifier | **5002** | `whoishoss.db` |
| `meeting_advisor/` _(planned)_ | Calls both services, recommends how to meet a subject in a given context | 5003 | — |

Each service owns its own blueprint, SQLAlchemy `db` instance, SQLite file,
data folder, and prompts — they can be deployed independently.

## Requirements

- Python 3.12+ (see `requirements.txt`)
- Docker + Docker Compose (optional, for the multi-service flow)
- OpenAI API key (for `/classify` and `/hoss`)

## Setup (local, without Docker)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env`:

- `DATABASE_URL` — whoiswhat DB (SQLite or PostgreSQL)
- `HOSS_DATABASE_URL` — whoishoss DB (separate SQLite file by default)
- `OPENAI_API_KEY` — required for both classifier UIs

Run **each service in its own terminal**:

```powershell
# terminal 1 — whoiswhat (K taxonomy)
python run.py                       # http://127.0.0.1:5000

# terminal 2 — whoishoss (HOSS)
python run_whoishoss.py             # http://127.0.0.1:5002
```

On first startup each service creates its tables and, if empty, imports its
data folder (`data/raw/` for whoiswhat, `data/hoss/` for whoishoss).

## Setup (Docker Compose — both services together)

```powershell
docker compose up --build
```

- whoiswhat → http://127.0.0.1:5001
- whoishoss → http://127.0.0.1:5002

Each service gets its own named volume (`whoiswhat_db`, `whoishoss_db`) so
the databases are independent and persist across restarts. `OPENAI_API_KEY`
is read from your host `.env`.

## WhoIsWhat (K taxonomy service)

Dataset files live in `data/raw/`:

| File | Role |
|------|------|
| `k_training_schema.json` | Evaluation criteria: task type, label space, dimensions, fields |
| `k_taxonomy_graph.json` | Taxonomy nodes + edges |
| `k_training_examples.jsonl` / `.csv` | Labeled training rows |

Endpoints:

| Endpoint | Description |
|----------|-------------|
| `GET /` | Index with links |
| `GET /classify` | UI — enter a subject name, two panels show K grouping + reasoning |
| `POST /api/v1/classify` | JSON `{"subject_name":"..."}` → structured classification |
| `GET /api/v1/evaluation-criteria` | Parsed `k_training_schema.json` |
| `GET /api/v1/taxonomy/graph` / `/nodes` / `/edges` | Taxonomy |
| `GET /api/v1/training-examples?limit=500` | Labeled examples |
| `GET /health` | DB connectivity |

Reimport the dataset at any time:

```powershell
flask --app wsgi import-k-data --force
```

## WhoIsHoss (HOSS F-scale classifier)

Dataset files live in `data/hoss/`:

| File | Role |
|------|------|
| `hoss_labels.json` | Weights, thresholds, item→dimension mapping |
| `f_scale_questions.json` | 30 F-scale-style items (1–6 scale) |
| `hoss_training_samples.jsonl` / `.csv` | Synthetic reference profiles |
| `hoss_classifier_system.txt` / `hoss_explainer_system.txt` | Prompts |
| `hoss_agent.example.json` | Example runtime config |
| `schema.sql` | Canonical SQL schema (mirrored by `whoishoss/models.py`) |

Pipeline (matches the HOSS starter README):

1. Classifier prompt → model infers `item_01..item_30` (1–6 each).
2. `scoring.py` deterministically computes **square**, **punisher**, **power**, **skull** from the item→dimension mapping.
3. `hoss_score = 0.20·square + 0.30·punisher + 0.25·power + 0.25·skull`.
4. Score is mapped to a **level (0–5)**, **display label**, and **internal label** via thresholds.
5. Explainer prompt produces the final narrative.
6. Result is persisted to `hoss_profiles` and the raw request/response pair to `hoss_runs`.

Endpoints:

| Endpoint | Description |
|----------|-------------|
| `GET /` | Index with links |
| `GET /hoss` | UI — name + optional source / notes; two panels show HOSS level + explanation |
| `POST /api/v1/hoss/classify` | JSON `{"name":"...", "source":"...", "input_summary":"..."}` |
| `GET /api/v1/hoss/labels` | Thresholds + weights + item mapping |
| `GET /api/v1/hoss/questions` | 30-item F-scale bank |
| `GET /api/v1/hoss/training-examples` | Synthetic reference profiles |
| `GET /api/v1/hoss/profiles` / `/<id>` | Stored classifications |
| `GET /health` | DB connectivity |

Reimport the HOSS dataset:

```powershell
flask --app wsgi_whoishoss import-hoss-data --force
```

**Safety**: classification is scoped to fictional characters, invented
personas, or opt-in self-reports — the classifier prompt enforces this.
Output is a stylized archetypal label, not a diagnosis.

## Planned: `meeting_advisor/`

A third microservice that calls both classifiers, merges the two structured
profiles with a user-supplied **meeting context** (setting, role, stakes,
goals), and asks an LLM for a meeting-preparation brief:

```
POST /api/v1/advise
{
  "subject_name": "...",
  "notes": "...",
  "context": {
    "setting": "work|social|family|negotiation|first-date|conflict",
    "your_role": "...",
    "stakes": "low|medium|high",
    "goals": "..."
  }
}
```

Returns `{risk_level, key_observations, do, dont, opening_move,
watchpoints, escalation_plan}`. Ships in a follow-up PR.

## Project layout

```
.
├── README.md
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── run.py                  # whoiswhat dev server
├── run_whoishoss.py        # whoishoss dev server
├── wsgi.py                 # whoiswhat WSGI
├── wsgi_whoishoss.py       # whoishoss WSGI
├── data/
│   ├── raw/                # K taxonomy + training source files
│   └── hoss/               # HOSS config, questions, prompts, samples
├── whoiswhat/              # K taxonomy classifier
│   ├── __init__.py         # create_app(), CLI
│   ├── extensions.py       # db (whoiswhat)
│   ├── models.py
│   ├── importer.py
│   ├── llm.py
│   └── routes.py
├── whoishoss/              # HOSS classifier
│   ├── __init__.py         # create_app(), CLI
│   ├── extensions.py       # db (whoishoss — separate instance)
│   ├── models.py
│   ├── scoring.py          # deterministic items→score→level pipeline
│   ├── importer.py
│   ├── llm.py              # uses hoss_classifier_system.txt + explainer
│   └── routes.py
├── .env.example
└── .env
```

## Optional next steps

- `meeting_advisor` aggregator microservice
- Flask-Migrate (Alembic) for schema evolution
- `pytest` suite and auth for non-public deployments
- Promote SQLite → PostgreSQL by changing only the `*_DATABASE_URL`
