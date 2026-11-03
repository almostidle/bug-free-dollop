# Plagiarism & AI Content Detector

A FastAPI application that detects plagiarism and AI-generated content using TF-IDF cosine similarity, Jaccard similarity, and heuristic text analysis.

## Prerequisites

- Python 3.11+
- PostgreSQL running locally

## Setup

1. **Create the database:**
   ```bash
   createdb plagiarism_detector
   ```

2. **Set up your environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Postgres credentials if they differ from the defaults
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Start the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

6. Open [http://localhost:8000](http://localhost:8000) in your browser.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/documents/analyze` | Submit text or .txt file for analysis |
| GET | `/api/documents/history` | List past submissions |
| GET | `/api/documents/{id}` | Get full results for a document |
| GET | `/api/config` | Read all detector configuration |
| PUT | `/api/config/{key}` | Update a config value |

## Configuration

All tunable parameters (shingle size, thresholds, metric weights, etc.) are stored in the `detector_config` database table and seeded by the Alembic migration. Use the config endpoints to read or update them at runtime—no restart required.

## How It Works

**Plagiarism Detection:**
- Normalizes text and splits into word shingles
- Compares against every stored document using Jaccard similarity on shingles and TF-IDF cosine similarity on full text
- Combines both scores using configurable weights and returns matched passages

**AI Content Detection (heuristic, no external API):**
- **Burstiness** — sentence length variance (uniform = AI-like)
- **Lexical Diversity** — type-token ratio (lower = AI-like)
- **Repeated N-grams** — proportion of repeated word n-grams
- **Average Sentence Length** — AI tends to cluster around medium lengths
- **Punctuation Patterns** — AI relies heavily on periods and commas
- Each metric is weighted and combined into an overall AI-likelihood score
