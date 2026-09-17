# AI Support Ticket Analytics System

## Overview

This repository implements the DOTMappers End-to-End AI System Sprint. It ingests the supplied 500-row support-ticket CSV, answers controlled natural-language analytics questions, detects anomalies, exposes a FastAPI REST API, and provides a Streamlit UI.

The central design choice is intentional: the LLM interprets language into a narrow JSON query, while Python and Pandas perform every filter, aggregate, rank, and anomaly calculation. The LLM never receives the CSV rows and never supplies numerical answers.

## Requirements implemented

- CSV ingestion, schema validation, and in-memory caching at startup
- Natural-language query pipeline using a locally runnable Ollama model
- Deterministic count, list, average, percentage, group, and top queries
- FastAPI endpoints for health, queries, and anomalies
- Streamlit UI that calls the API rather than duplicating business logic
- Business-rule and IQR-based anomaly detection
- Unit, parser, API, security, and end-to-end-with-fake-LLM tests
- Docker Compose configuration and local zero-cost operation

## Architecture

```text
Streamlit UI ──HTTP──> FastAPI
                         │
                 StructuredQueryParser ──> Ollama (schema and question only)
                         │
                     Pydantic + allowlists
                         │
          Pandas QueryEngine <──> AnomalyDetector
                         │
              data/support_tickets.csv (loaded once)
```

The query layer is isolated behind `QueryEngine`, so a future production deployment can replace Pandas with PostgreSQL without changing the API or LLM boundary.

## Project structure

```text
app/
  main.py                   FastAPI app and routes
  config.py                 environment-backed configuration
  models.py                 request, response, and structured-query schemas
  data/                     loader, schema validator, deterministic query engine
  llm/                      Ollama client, prompt, and validated parser
  anomalies/detector.py     business-rule and IQR detector
  services/query_service.py query pipeline orchestration
ui/streamlit_app.py         minimal API-backed UI
data/support_tickets.csv    supplied assessment data
tests/                      deterministic, parser, API, anomaly, security tests
```

## Technology choices

- **FastAPI** provides typed HTTP routes and automatic OpenAPI documentation at `/docs`.
- **Streamlit** provides a deliberately small analyst-facing UI.
- **Pandas** is appropriate for the supplied 500 rows and keeps deterministic operations straightforward.
- **Ollama** provides a local, zero-cost LLM option. `LLMClient` isolates the rest of the application from Ollama details.
- **Pydantic** validates request bodies and model-generated structured queries before any data operation occurs.

## Data model and validation

The loader requires exactly the assessment fields: `ticket_id`, `created_at`, `category`, `priority`, `status`, `response_time_hrs`, `resolution_time_hrs`, `agent_id`, `customer_rating`, and `issue_summary`.

It validates unique IDs; datetimes; category, priority, and status allowlists; non-negative time values; and rating range 1–5. It explicitly preserves the 173 legitimate null `resolution_time_hrs` and `customer_rating` values for unresolved tickets. Nulls are excluded from averages rather than converted to zero.

## Query design

The controlled internal query format allows only known operations, fields, operators, enum values, a 100-row maximum result, and safe substring matching only for `issue_summary`. It does not expose SQL or Python execution.

Relative time is evaluated against the historical dataset reference timestamp, not the computer clock. For the supplied CSV that timestamp is **2024-03-30T18:06:00**. Thus, “this month” means March 2024 and “this week” means Monday 2024-03-25 through Monday 2024-04-01.

An implementation decision for the phrasing “not resolved within 12 hours”: it returns both unresolved Critical tickets and resolved Critical tickets whose `resolution_time_hrs` exceeds 12. This is documented because the assessment wording leaves the unresolved case ambiguous.

## LLM and security design

Ollama receives the user question, supported schema, allowlists, date semantics, and strict system instructions. It never receives the 500 ticket rows or secrets. The parser validates its JSON twice at most, rejects unknown fields/operations, and then sends only a validated `StructuredQuery` to Pandas.

The system rejects common prompt-injection and unsafe-execution requests before calling the model; rejects malformed or extra model output; limits question length to 500 characters; never evaluates model code; never runs model SQL; and does not reveal prompts, environment variables, or exception traces. Ticket `issue_summary` is only searched by deterministic, literal substring matching after query validation.

If Ollama is unavailable, `/health` still reports the API as healthy with `llm_status: unavailable`; `/query` returns HTTP 503 instead of attempting a fabricated answer.

## Anomaly methodology

Two deterministic detectors run separately from natural-language querying:

1. **Business rule:** Open or Escalated High/Critical tickets whose age exceeds 24 hours relative to the dataset reference timestamp.
2. **Statistical:** Resolved tickets with `resolution_time_hrs > Q3 + 1.5 × IQR`. Unresolved null resolution times never influence the IQR.

For this dataset, the statistical upper bound is **48.15 hours**. The full data contains 80 business-rule anomalies and 21 statistical anomalies.

## Setup

Prerequisite: Python 3.11+.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

For natural-language queries, install [Ollama](https://ollama.com/), start it, and pull the configured local model:

```bash
ollama pull llama3.2:latest
```

Set `OLLAMA_MODEL` in `.env` if a different local model is used. No API key is needed.
The default `LLM_TIMEOUT_SECONDS=120` accommodates a cold local-model load; reduce it if the model is already resident and a shorter failure window is preferred.

## Running locally

Start the API:

```bash
.venv/bin/uvicorn app.main:app --reload
```

In another terminal, start the UI:

```bash
.venv/bin/streamlit run ui/streamlit_app.py
```

Visit `http://localhost:8501` for the UI and `http://localhost:8000/docs` for the API docs.

To start API and UI together with Docker, with Ollama running on the host:

```bash
docker compose up --build
```

The UI is available at `http://localhost:8501`. Docker routes its API service to host Ollama through `host.docker.internal`.

## API

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/health` | API/data health, counts, reference timestamp, LLM availability |
| `POST` | `/query` | Natural-language question to validated deterministic result |
| `GET` | `/anomalies?type=all|business|statistical` | Deterministic anomaly records |

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/query -H 'content-type: application/json' -d '{"question":"How many tickets are currently open?"}'
curl 'http://localhost:8000/anomalies?type=statistical'
```

## Example queries and actual outputs

These were computed against the supplied data, not invented by an LLM.

| Question | Deterministic result |
| --- | --- |
| How many tickets are currently open? | 111 |
| Which agent resolved the most tickets this month? | AGT-01, 16 resolved tickets in March 2024 |
| Show me all Critical tickets not resolved within 12 hours. | 34 matching tickets |
| What is the average customer rating for Technical category tickets? | 3.74 |
| Are there any anomalies in resolution times this week? | 5 statistical resolution-time anomalies: TKT-108, TKT-130, TKT-158, TKT-255, TKT-400 |

Additional supported examples include “How many critical tickets are unresolved?”, “Which category has the most tickets?”, “How many tickets were created in February?”, and “Show tickets mentioning invoice.”

## Testing

Run the full suite without Ollama, credentials, or internet:

```bash
.venv/bin/pytest
```

Tests cover actual CSV loading and null semantics, query ground truth, date filters, IQR behavior, mocked LLM parsing and retry, API endpoints, malformed requests, unavailable LLM behavior, and hostile prompt-injection examples.

## Known limitations

- The local model must be installed and running for real natural-language queries. The repository deliberately does not silently fall back to a rules-only parser in production.
- Prompt injection mitigation is defense in depth, not a claim of perfect protection against every future model behavior.
- The structured query language targets the assessment analytics set, not arbitrary analytics or conversational follow-ups.
- Pandas is appropriate for 500 rows but a larger concurrent production workload would use a database, authentication, rate limits, observability, and a model gateway.
- Docker Compose expects a host Ollama installation rather than attempting to package a model download in the application image.

## Walkthrough talking points

1. The LLM knows the schema and translates language; the deterministic query engine knows the data and calculates truth.
2. No RAG or vector database is needed because this is a small structured analytics problem, not semantic document retrieval.
3. The strict Pydantic schema and allowlists are the key security boundary between model output and data execution.
4. Historical relative-time semantics are anchored to the dataset’s latest timestamp, producing reproducible results.
5. Business-rule anomalies make an operational SLA concern explicit, while IQR supplies a data-driven slow-resolution signal.
