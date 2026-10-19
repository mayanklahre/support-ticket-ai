# Threats, risks, and controls

| Risk / threat | Impact | Control | Residual limit |
| --- | --- | --- | --- |
| Prompt injection attempts | Model may be induced to ignore instructions or request unsafe actions. | Reject unsafe patterns; use a narrow schema; validate model output; never evaluate model code or SQL. | Defence in depth is not a guarantee against every future model behaviour. |
| Invalid or malformed query | Incorrect or uncontrolled data operation. | Field/operator/enum allowlists, Pydantic validation, question-length bound, controlled 400 responses. | Supported query language remains deliberately limited. |
| Ticket-row exposure to model | Confidential data may be transferred or retained. | Keep CSV rows inside deterministic Python/Pandas layer; provide only schema and user question to Ollama. | Deployment still needs access control and data governance. |
| Unavailable or slow model | User receives fabricated or delayed answers. | Health endpoint reports model state; query endpoint returns 503 when unavailable; timeouts are configured. | Local model dependency remains operationally required. |
| Incorrect anomaly interpretation | Poor support decision from a statistical flag. | Separate business-rule and IQR detectors; document thresholds and return evidence. | Anomaly flags require human context and review. |
| Scale/concurrency limitations | Slow or unstable production workload. | Scope to supplied 500 rows; future path is database, authentication, rate limits, observability, and model gateway. | Current project is not production infrastructure. |
