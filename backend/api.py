#!/usr/bin/env python3
"""FastAPI read API over ClickHouse (Enterprise Analytics)."""

from __future__ import annotations

from typing import Any

import clickhouse_connect
from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Summary, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response, Security, Depends
from fastapi.security import APIKeyHeader
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
import logging
from pythonjsonlogger import jsonlogger

# OpenTelemetry Tracing
OTEL_COLLECTOR = os.getenv("OTEL_COLLECTOR", "jaeger:4317")

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource

def init_tracer():
    resource = Resource.create(attributes={
        "service.name": "backend-api"
    })
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=OTEL_COLLECTOR, insecure=True))
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

init_tracer()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NTA_")

    ch_host: str = Field(default="localhost", description="ClickHouse HTTP host")
    ch_port: int = Field(default=8123, description="ClickHouse HTTP port")
    ch_user: str = Field(default="default")
    ch_password: str = Field(default="NTI_Secure_2026")
    api_key: str = Field(default="admin-api-key", description="Master API Key")


settings = Settings()

# Structured Logging
log = logging.getLogger("api")
log.setLevel(logging.INFO)
if not log.handlers:
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)

# Security
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key
app = FastAPI(
    title="Network Telemetry API",
    description="Enterprise API for aggregated metrics in ClickHouse.",
    version="0.1.0",
)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Prometheus metrics
REQUESTS = Counter("nta_http_requests_total", "Total HTTP requests", ["path"])
LATENCY = Summary("nta_http_latency_seconds", "HTTP request latency", ["path"])


@app.get("/metrics")
def metrics() -> Response:
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


def get_client() -> Any:
    return clickhouse_connect.get_client(
        host=settings.ch_host,
        port=settings.ch_port,
        username=settings.ch_user,
        password=settings.ch_password,
    )


@app.get("/health")
def health() -> dict[str, str]:
    try:
        get_client().command("SELECT 1")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"clickhouse: {e}") from e
    return {"status": "ok"}


@app.get("/api/v1/top-talkers")
def top_talkers(
    limit: int = 10,
    api_key: str = Depends(get_api_key)
) -> list[dict[str, Any]]:
    """Top source IPs by total bytes (Optimized via Materialized View)."""
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be 1..500")
    client = get_client()
    REQUESTS.labels(path="/api/v1/top-talkers").inc()
    with LATENCY.labels(path="/api/v1/top-talkers").time():
        q = """
        SELECT
            toString(src_ip) AS src_ip,
            sumMerge(total_bytes) AS total_bytes,
            sumMerge(total_packets) AS total_packets,
            max(last_seen) AS last_seen
        FROM network_telemetry.top_talkers
        GROUP BY src_ip
        ORDER BY total_bytes DESC
        LIMIT %(lim)s
        """
        result = client.query(q, parameters={"lim": limit})
    return [dict(zip(result.column_names, row)) for row in result.result_rows]


@app.get("/api/v1/bandwidth-per-minute")
def bandwidth_per_minute(
    minutes: int = 15,
    api_key: str = Depends(get_api_key)
) -> list[dict[str, Any]]:
    """Bandwidth time series (Optimized via Materialized View)."""
    if minutes < 1 or minutes > 1440:
        raise HTTPException(status_code=400, detail="minutes must be 1..1440")
    client = get_client()
    REQUESTS.labels(path="/api/v1/bandwidth-per-minute").inc()
    with LATENCY.labels(path="/api/v1/bandwidth-per-minute").time():
        q = """
        SELECT
            minute,
            sumMerge(total_bytes) AS total_bytes,
            sumMerge(total_packets) AS total_packets
        FROM network_telemetry.bandwidth_minutely
        WHERE minute >= now() - toIntervalMinute(%(mins)s)
        GROUP BY minute
        ORDER BY minute ASC
        """
        result = client.query(q, parameters={"mins": minutes})
    return [dict(zip(result.column_names, row)) for row in result.result_rows]
