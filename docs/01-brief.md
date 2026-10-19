# Project brief

**Project:** AI Support Ticket Analytics System  
**Delivery:** Solo project using the supplied 500-row assessment dataset.

## Problem and users
Support leads need reliable answers about ticket volumes, status, resolution time, customer rating, and anomalies without granting an LLM unrestricted access to data operations. The intended user is an analyst or support manager working with the supplied structured ticket dataset.

## Goal and success criteria
Translate approved natural-language questions into a narrow, validated query format; calculate results deterministically with Python/Pandas; surface anomaly records; and provide an API and small UI. The model must never receive ticket rows or produce the calculated result.

## Scope
**In:** CSV ingestion/validation, controlled natural-language questions, deterministic queries, anomaly detection, FastAPI, Streamlit, tests, Docker Compose.

**Out:** arbitrary code/SQL execution, user authentication, production data operations, multi-tenant access, and general-purpose conversational analytics.

## Safety principle
The LLM receives a question plus approved schema/allowlists. Pydantic and allowlists validate the proposed structured query before Pandas performs any calculation. Ticket rows remain outside the model context.
