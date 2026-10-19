# Retrospective

**Retrospective documentation, written on 19 October 2026.** This describes the finished solo repository and is not backdated sprint evidence.

## What worked
- Separating language interpretation from deterministic calculation created a clear safety and accuracy boundary.
- Pydantic and allowlists made the permitted analytics surface visible and testable.
- API, UI, Docker Compose, and 25 tests made the project reproducible locally.

## What was difficult
- Natural language is broad while safe data operations must be narrow; explicit schema limits were necessary.
- Relative date questions against historical data required a fixed dataset reference timestamp.
- A local LLM removes external API cost but adds setup and availability dependency.

## Improvements
- Replace in-memory Pandas with a database for larger/concurrent workloads.
- Add authentication, authorisation, rate limits, observability, and a model gateway for a real deployment.
- Expand the query schema only through documented requirements, validation, and tests.
- Perform independent security testing before handling real customer data.
