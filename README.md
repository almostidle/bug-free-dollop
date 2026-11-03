# Plagiarism & AI Content Detector

A FastAPI web application that detects **corpus-based & pairwise plagiarism** alongside **AI-generated writing signals** using word-shingle Jaccard similarity, corpus-wide bigram TF-IDF cosine similarity, character-aligned span highlighting, and a 5-feature linguistic heuristic model.

---

## Key Features

- **Hybrid Plagiarism Engine**
  - **Word-Shingle Jaccard Similarity** catches verbatim and lightly edited phrase reuse (`k`-word sliding shingles).
  - **Corpus-Level Bigram TF-IDF Cosine Similarity** fits unigrams + bigrams (`ngram_range=(1, 2)`, sublinear TF scaling) across the stored corpus in a single pass to capture lexical/topical overlap and paraphrasing.
  - **Character-Aligned Inline Highlighting** maps matched shingle intervals back to exact `(start, end)` character offsets in the submitted document.
  - **Direct Pairwise Comparison** (`/api/documents/compare`) compares any Reference text against a Suspect submission without altering the stored corpus.
- **Linguistic AI Content Detection (No External API Required)**
  - **Burstiness (Sentence Length CV)** — measures sentence-length coefficient of variation (abbreviation- and decimal-aware sentence segmentation).
  - **Moving-Average Type-Token Ratio (MATTR)** — 50-word sliding-window lexical diversity that avoids Heap's Law length bias on longer essays.
  - **Repeated Word N-grams** — detects formulaic LLM transitional phrases.
  - **Mean Sentence Length** — flags prose tightly clustered around typical 16–22 word LLM cadence.
  - **Punctuation Diversity** — compares basic marks (`.,:`) against expressive human punctuation (`—;!?()`).
- **Interactive Demo & Runtime Configuration**
  - Pre-seeded CS academic reference corpus + 4 one-click demo scenarios (*Clean Human*, *Patchwork Multi-Source Plagiarism*, *Uniform AI Prose*, *Paraphrased Technical Summary*).
  - Live runtime tuning of thresholds, shingle sizes, and heuristic weights via `/api/config` and the **Detector Parameters** tab—no server restart required.

---

## Quickstart (Zero-Setup SQLite Demo)

```bash
# 1. Create virtual environment & install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# 2. Start the server (auto-initializes SQLite & seeds 4 reference papers)
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) for the interactive dashboard, or [http://localhost:8000/docs](http://localhost:8000/docs) for the OpenAPI Swagger UI.

### Using PostgreSQL + Alembic

```bash
createdb plagiarism_detector
cp .env.example .env
# Uncomment DATABASE_URL=postgresql://postgres:postgres@localhost:5432/plagiarism_detector in .env
alembic upgrade head
uvicorn app.main:app --reload
```

---

## Running Tests

```bash
pytest -v
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Service health and version check |
| `POST` | `/api/documents/analyze` | Analyze text or `.txt`/`.md` upload (`save_to_corpus` optional) |
| `POST` | `/api/documents/compare` | Direct side-by-side comparison of reference vs. suspect text |
| `GET` | `/api/documents/stats` | Corpus counts, flagged totals, and active thresholds |
| `GET` | `/api/documents/history` | List stored corpus & past submissions |
| `GET` | `/api/documents/{id}` | Retrieve full document content and stored analysis report |
| `DELETE` | `/api/documents/{id}` | Remove a document from the corpus |
| `GET` | `/api/config` | List all runtime detector parameters |
| `PUT` | `/api/config/{key}` | Validate and update a detector parameter at runtime |
| `POST` | `/api/config/reset` | Restore all detector parameters to default values |
| `GET` | `/api/demo/samples` | Fetch built-in demo test scenarios |
| `POST` | `/api/demo/seed` | Seed or reset (`?reset=true`) the academic reference corpus |

---

## Project Structure

```text
app/
├── api/          # FastAPI routers (documents, config, demo)
├── db/           # SQLAlchemy engine, session, and DB initialization
├── models/       # ORM models (Document, DetectorConfig)
├── schemas/      # Pydantic v2 request/response schemas
├── services/     # Plagiarism, AI detection, config, document, & demo services
├── static/       # Interactive single-page frontend dashboard
└── utils/        # Text normalizer, span tokenizer, shingling, & TF-IDF similarity
alembic/          # Database schema & seed migrations
tests/            # Pytest unit & API integration suite
```
