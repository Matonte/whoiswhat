# WhoIsWhat — monorepo

Two Flask microservices and (planned) an aggregator, designed as a work-sample
project that classifies subjects along two independent taxonomies:

| Service | Role | Port | DB |
|---|---|---|---|
| [`whoiswhat/`](./whoiswhat) | K-taxonomy classifier (criteria + labeled examples) | **5001** (docker) / 5000 (local) | `whoiswhat.db` |
| [`whoishoss/`](./whoishoss) | HOSS F-scale archetype classifier | **5002** | `whoishoss.db` |
| [`meeting_advisor/`](./meeting_advisor) | Aggregator — calls both classifiers over HTTP + LLM meeting guidance | **5003** | `meeting_advisor.db` |

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

# terminal 3 — meeting_advisor (calls both over HTTP)
python run_meeting_advisor.py       # http://127.0.0.1:5003
```

On first startup each service creates its tables and, if empty, imports its
data folder (`data/raw/` for whoiswhat, `data/hoss/` for whoishoss).

## Setup (Docker Compose — both services together)

```powershell
docker compose up --build
```

- whoiswhat → http://127.0.0.1:5001
- whoishoss → http://127.0.0.1:5002
- meeting_advisor → http://127.0.0.1:5003 (reaches its siblings via Docker DNS: `http://whoiswhat:5000`, `http://whoishoss:5002`)

Each service gets its own named volume (`whoiswhat_db`, `whoishoss_db`,
`advisor_db`) so the databases are independent and persist across restarts.
`OPENAI_API_KEY` is read from your host `.env`.

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

## Meeting Advisor (aggregator)

`meeting_advisor/` is a true sibling microservice: it calls WhoIsWhat and
WhoIsHoss **over HTTP**, caches the two profiles in its own SQLite DB with
a configurable TTL, opportunistically reuses already-persisted HOSS
profiles (avoiding a re-classification), and asks the LLM for a
tactical meeting brief.

Request:

```
POST /api/v1/advise
{
  "subject_name": "...",
  "source_hint": "Breaking Bad | invented | work colleague ...",  // optional
  "notes": "optional behavior notes, forwarded to both classifiers",
  "context": {
    "setting": "work|social|family|negotiation|first-date|conflict|interview|other",
    "stakes": "low|medium|high",
    "your_role": "...",
    "goals": "..."
  }
}
```

Response (standard schema):

```json
{
  "id": 7,
  "k_profile":    { ... full WhoIsWhat /classify response ... },
  "hoss_profile": { ... full WhoIsHoss /hoss/classify response ... },
  "advice": {
    "risk_level": "low|medium|high",
    "key_observations": "...",
    "do":   ["...", "..."],
    "dont": ["...", "..."],
    "opening_move": "...",
    "watchpoints": ["...", "..."],
    "escalation_plan": "..."
  }
}
```

Endpoints:

| Endpoint | Description |
|----------|-------------|
| `GET /` | Index |
| `GET /advise` | UI — subject + notes + meeting context; two panels for profiles, one for guidance |
| `POST /api/v1/advise` | Fan-out + LLM brief (see above) |
| `GET /api/v1/advice` | List stored advice runs |
| `GET /api/v1/advice/<id>` | Full detail of a stored run (context + both profiles + advice JSON) |
| `GET /health` | DB connectivity + resolved sibling URLs |

Safety: the advisor's system prompt refuses manipulative, coercive,
illegal, or harm-directed guidance and never echoes raw profile JSON to
the caller.

## Project layout

```
.
├── README.md
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── run.py                    # whoiswhat dev server
├── run_whoishoss.py          # whoishoss dev server
├── run_meeting_advisor.py    # meeting_advisor dev server
├── wsgi.py                   # whoiswhat WSGI
├── wsgi_whoishoss.py         # whoishoss WSGI
├── wsgi_meeting_advisor.py   # meeting_advisor WSGI
├── data/
│   ├── raw/                  # K taxonomy + training source files
│   └── hoss/                 # HOSS config, questions, prompts, samples
├── whoiswhat/                # K taxonomy classifier
│   ├── __init__.py           # create_app(), CLI
│   ├── extensions.py         # db (whoiswhat)
│   ├── models.py
│   ├── importer.py
│   ├── llm.py
│   └── routes.py
├── whoishoss/                # HOSS classifier
│   ├── __init__.py           # create_app(), CLI
│   ├── extensions.py         # db (whoishoss — separate instance)
│   ├── models.py
│   ├── scoring.py            # deterministic items→score→level pipeline
│   ├── importer.py
│   ├── llm.py                # uses hoss_classifier_system.txt + explainer
│   └── routes.py
├── meeting_advisor/          # Aggregator / HTTP orchestrator
│   ├── __init__.py           # create_app()
│   ├── extensions.py         # db (advisor — separate instance)
│   ├── models.py             # subject_cache + advice_runs
│   ├── clients.py            # HTTP clients for the two sibling services
│   ├── llm.py                # merged-profile → meeting brief
│   └── routes.py
├── .env.example
└── .env
```

## Optional next steps

- Flask-Migrate (Alembic) for schema evolution
- `pytest` suite and auth for non-public deployments
- Promote SQLite → PostgreSQL by changing only the `*_DATABASE_URL`
- Persist WhoIsWhat classifications so the advisor can reuse them too
- Rate limiting and request IDs for cross-service tracing
