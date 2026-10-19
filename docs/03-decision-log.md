# Decision log

| ID | Decision | Options considered | Choice and rationale | Consequence |
| --- | --- | --- | --- | --- |
| D-01 | Model location | Hosted model; local Ollama; no language layer | **Local Ollama** enables low-cost local operation and reduces data-transfer exposure for the supplied dataset. | A local model must be installed and running. |
| D-02 | Query boundary | Model writes code/SQL; unrestricted natural-language answer; structured schema | **Allow-listed structured query schema** limits operations, fields, filters, and result size. | Coverage is intentionally narrower than open-ended analytics. |
| D-03 | Validation | Trust model JSON; Pydantic plus allowlists; manual review | **Pydantic validation and allowlists** reject unknown operations, fields, values, and malformed output before data access. | New analytical capabilities require explicit schema changes. |
| D-04 | Calculation engine | LLM calculation; deterministic Pandas; database from day one | **Deterministic Pandas** makes calculations reproducible for 500 rows and keeps the model away from numeric truth. | Larger concurrent datasets need a database later. |
| D-05 | Relative dates | Computer clock; dataset reference timestamp | **Dataset reference timestamp** ensures results are reproducible against historical assessment data. | Semantics must be documented to users. |
