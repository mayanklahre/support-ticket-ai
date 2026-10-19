# AI Support Ticket Analytics System

**Solo project | Local-first analytics for the supplied 500-row support-ticket dataset**

## Problem
Support teams need dependable answers about ticket status, response/resolution time, ratings, and anomalies. A language model can make the interface easier, but it should not receive ticket rows or be trusted to calculate business results.

## Who it is for
An analyst or support lead using the supplied assessment dataset who needs controlled natural-language analytics plus deterministic, inspectable results.

## Goal and success criteria
Translate a supported question into a validated structured query, then have Python/Pandas perform every calculation. The model receives only the question, schema, and allowlists—not ticket rows—and never generates numeric results.

## Scope
**In scope:** CSV ingestion/validation, local Ollama intent parsing, allow-listed queries, deterministic Pandas calculations, anomaly detection, FastAPI, Streamlit, Docker Compose, and 25 tests.

**Out of scope:** arbitrary code/SQL execution, unrestricted conversational analytics, production authentication, multi-tenant access, and enterprise-scale data operations.

## Key decisions
- Local Ollama interprets language without sending the supplied data rows to a hosted model.
- A Pydantic-validated, allow-listed query schema controls the actions an LLM may request.
- Pandas calculates all results deterministically.
- Business-rule and IQR anomalies remain separate and documented.

See the [decision log](docs/03-decision-log.md).

## Outcome
The repository provides an API, Streamlit UI, controlled query path, anomaly endpoints, Docker Compose configuration, and **25 automated tests**. Example figures reported in the repository are calculated from the supplied assessment data; they are not claims about a production support team.

## Risks and mitigations
The main risks are prompt injection, invalid queries, data exposure, unavailable local models, and misuse of anomaly flags. Mitigations include a narrow schema, Pydantic validation, allowlists, controlled errors, and keeping CSV rows outside the model context. See [threats and risks](docs/04-risks.md).

## How to run
Requirements: Python 3.11+ and Ollama for live natural-language queries.

    python3 -m venv .venv
    .venv/bin/python -m pip install -r requirements.txt
    cp .env.example .env
    ollama pull llama3.2:latest
    .venv/bin/uvicorn app.main:app --reload

In another terminal:

    .venv/bin/streamlit run ui/streamlit_app.py

Run the full test suite without Ollama, credentials, or internet:

    .venv/bin/pytest

Use docker compose up --build to start API and UI together with Ollama available on the host.

## Next steps
- Move to a database for larger/concurrent workloads.
- Add authentication, authorisation, rate limits, observability, and model-gateway controls.
- Expand supported queries only with explicit requirements and test coverage.
- Complete independent security testing before real customer-data use.

## Documentation
- [Brief](docs/01-brief.md)
- [Requirements](docs/02-requirements.md)
- [Decision log](docs/03-decision-log.md)
- [Risks](docs/04-risks.md)
- [Quality and tests](docs/05-quality-and-tests.md)
- [Retrospective](docs/06-retrospective.md)
