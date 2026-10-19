# Requirements and acceptance criteria

| ID | User story | Acceptance criteria |
| --- | --- | --- |
| RQ-01 | As an analyst, I can ask approved natural-language ticket questions. | The API accepts a bounded question and returns a result only when it can be parsed into a supported query schema. |
| RQ-02 | As an analyst, I receive deterministic results. | Python/Pandas, not the LLM, performs filters, counts, averages, groups, rankings, and anomaly calculations. |
| RQ-03 | As a security-conscious user, my ticket rows are not sent to the model. | Ollama receives only the question, supported schema, allowlists, date semantics, and instructions—not the CSV rows. |
| RQ-04 | As an analyst, I can inspect anomalies. | Business-rule and IQR anomaly endpoints return records with documented criteria. |
| RQ-05 | As an operator, I can see whether dependencies are ready. | Health endpoint reports data state and LLM availability; unavailable LLM returns a controlled 503 for queries. |
| RQ-06 | As a maintainer, I can run the application locally. | FastAPI, Streamlit, Docker Compose, environment configuration, and test commands are documented. |

## Requirement-to-test traceability
The repository contains **25 pytest tests** mapped as follows: security 6; queries 4; anomalies 4; parser 3; API 3; data 3; end-to-end 1; model defaults 1. A test passing proves the represented scenario, not unrestricted safety or production readiness.
