from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from app.anomalies.detector import AnomalyDetector
from app.config import Settings, get_settings
from app.data.loader import dataset_metadata, load_tickets
from app.data.query_engine import QueryEngine, QueryExecutionError
from app.llm.client import LLMUnavailableError, build_llm_client
from app.llm.parser import QueryParseError, StructuredQueryParser
from app.models import AnomalyResponse, HealthResponse, QueryRequest, QueryResponse
from app.services.query_service import QueryService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, llm_client=None) -> FastAPI:
    settings = settings or get_settings()
    dataframe = load_tickets(settings.data_path)
    client = llm_client or build_llm_client(settings)
    detector = AnomalyDetector(dataframe)
    service = QueryService(QueryEngine(dataframe, settings.max_list_rows), StructuredQueryParser(client), detector, detector.reference_timestamp)
    metadata = dataset_metadata(dataframe)
    app = FastAPI(title="AI Support Ticket Analytics", version="1.0.0")
    app.state.llm_client = client
    app.state.query_service = service
    app.state.detector = detector
    app.state.metadata = metadata

    @app.exception_handler(QueryParseError)
    async def query_parse_error_handler(_, exc: QueryParseError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(QueryExecutionError)
    async def query_execution_error_handler(_, exc: QueryExecutionError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="healthy", record_count=metadata["record_count"], llm_provider=settings.llm_provider,
                              llm_status="available" if client.is_available() else "unavailable",
                              dataset_reference_date=detector.reference_timestamp.isoformat(),
                              status_counts={key: int(value) for key, value in dataframe["status"].value_counts().items()})

    @app.post("/query", response_model=QueryResponse)
    def query(request: QueryRequest) -> QueryResponse:
        try:
            return service.answer(request.question)
        except LLMUnavailableError as exc:
            raise HTTPException(status_code=503, detail="The configured LLM service is unavailable. Start Ollama and pull the configured model.") from exc

    @app.get("/anomalies", response_model=AnomalyResponse)
    def anomalies(type: str = Query(default="all", pattern="^(all|business|statistical)$")) -> AnomalyResponse:
        return detector.detect(type)

    return app


app = create_app()
