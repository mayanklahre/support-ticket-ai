# v1.0.0 release notes

**Release notes prepared on 19 October 2026.**

## Shipped
- Local FastAPI and Streamlit support-ticket analytics flow.
- Local Ollama intent parsing behind Pydantic/allow-list validation.
- Deterministic Pandas query engine, business-rule/IQR anomaly detection, Docker Compose, and 25 tests.

## Known limits
- Works with the supplied 500-row dataset and a controlled query language.
- Requires local Ollama for live natural-language queries.
- Not a multi-user, production deployment; authentication, database scale, rate limits, and observability are future work.

## Handover
Repository includes local setup, tests, safety boundary documentation, requirements, decisions, risks, and retrospective.
