# Quality and tests

## Quality strategy
Critical calculations are deterministic and testable; the model is constrained to intent parsing. Tests run without Ollama, credentials, or internet by using deterministic paths and mocked LLM behaviour where required.

| Test group | Count | Requirement evidence |
| --- | ---:| --- |
| Security | 6 | Injection/unsafe-execution rejection and safe boundaries |
| Queries | 4 | Ground-truth query outcomes and date semantics |
| Anomalies | 4 | Business-rule and IQR detection behaviour |
| Parser | 3 | Valid structured parsing and malformed-model-output handling |
| API | 3 | Health, query, and error contracts |
| Data | 3 | CSV schema, null semantics, and validation |
| End-to-end | 1 | Complete workflow with fake LLM |
| Model defaults | 1 | Default model/configuration behaviour |
| **Total** | **25** | Repository test suite |

## Manual checks
1. Start API and Streamlit locally.
2. Confirm health reports data and LLM state.
3. Run a supported question and compare output with documented ground truth.
4. Send an unsupported/injection-style request and confirm safe rejection.
5. Verify no ticket rows are included in the Ollama request path.
6. Check business-rule and statistical anomaly responses separately.

## Quality limits
The supplied dataset and controlled schema are appropriate for the project scope. They do not establish enterprise-scale performance, multi-user security, or universal resistance to prompt injection.
