#!/usr/bin/env python3
"""Consume network-telemetry from Kafka and batch-insert into ClickHouse (MergeTree)."""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from datetime import datetime, timezone
from typing import Any

import clickhouse_connect
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from codec import decode_metric

import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

# OpenTelemetry Tracing
OTEL_COLLECTOR = os.getenv("OTEL_COLLECTOR", "jaeger:4317")

def init_tracer():
    resource = Resource.create(attributes={
        "service.name": "kafka-sink"
    })
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=OTEL_COLLECTOR, insecure=True))
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

init_tracer()
tracer = trace.get_tracer("kafka-sink")

import logging
from pythonjsonlogger import jsonlogger

# Structured Logging
log = logging.getLogger("sink")
log.setLevel(logging.INFO)
if not log.handlers:
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)

DDL = """
CREATE DATABASE IF NOT EXISTS network_telemetry;

CREATE TABLE IF NOT EXISTS network_telemetry.network_metrics
(
    ts DateTime64(3, 'UTC'),
    src_ip IPv4,
    dst_ip IPv4,
    src_port UInt16,
    dst_port UInt16,
    protocol LowCardinality(String),
    bytes UInt64,
    packets UInt64,
    ingested_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMMDD(ts)
ORDER BY (ts, src_ip, dst_ip, dst_port, protocol)
TTL toDateTime(ts) + INTERVAL 180 DAY;

-- Enterprise Aggregations
CREATE TABLE IF NOT EXISTS network_telemetry.top_talkers
(
    src_ip IPv4,
    total_bytes AggregateFunction(sum, UInt64),
    total_packets AggregateFunction(sum, UInt64),
    last_seen SimpleAggregateFunction(max, DateTime64(3, 'UTC'))
)
ENGINE = AggregatingMergeTree
ORDER BY src_ip;

CREATE MATERIALIZED VIEW IF NOT EXISTS network_telemetry.mv_top_talkers
TO network_telemetry.top_talkers
AS SELECT
    src_ip,
    sumState(bytes) AS total_bytes,
    sumState(packets) AS total_packets,
    maxSimpleState(ts) AS last_seen
FROM network_telemetry.network_metrics
GROUP BY src_ip;

CREATE TABLE IF NOT EXISTS network_telemetry.bandwidth_minutely
(
    minute DateTime,
    total_bytes AggregateFunction(sum, UInt64),
    total_packets AggregateFunction(sum, UInt64)
)
ENGINE = AggregatingMergeTree
ORDER BY minute;

CREATE MATERIALIZED VIEW IF NOT EXISTS network_telemetry.mv_bandwidth_minutely
TO network_telemetry.bandwidth_minutely
AS SELECT
    toStartOfMinute(ts) AS minute,
    sumState(bytes) AS total_bytes,
    sumState(packets) AS total_packets
FROM network_telemetry.network_metrics
GROUP BY minute;
"""


def parse_ts(raw: str) -> datetime:
    raw = raw.replace("Z", "+00:00")
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def row_from_payload(obj: dict[str, Any]) -> list[Any]:
    return [
        parse_ts(obj["ts"]),
        obj["src_ip"],
        obj["dst_ip"],
        int(obj["src_port"]),
        int(obj["dst_port"]),
        str(obj["protocol"]),
        int(obj["bytes"]),
        int(obj["packets"]),
    ]


def ensure_schema(client: Any) -> None:
    for stmt in (s.strip() for s in DDL.split(";") if s.strip()):
        client.command(stmt)
    log.info("ClickHouse schema OK")


def main() -> None:
    p = argparse.ArgumentParser(description="Kafka → ClickHouse sink")
    p.add_argument("--kafka", default="localhost:9092", help="Kafka bootstrap")
    p.add_argument("--topic", default="network-telemetry-avro")
    p.add_argument("--group", default="nti-sync-v1")
    p.add_argument("--ch-host", default="localhost")
    p.add_argument("--ch-port", type=int, default=8123)
    p.add_argument("--ch-user", default="default")
    p.add_argument("--ch-password", default="NTI_Secure_2026")
    p.add_argument("--batch-size", type=int, default=100)
    p.add_argument("--flush-interval", type=float, default=2.0)
    p.add_argument("--kafka-tls", action="store_true", help="Enable TLS for Kafka connection")
    p.add_argument("--kafka-tls-insecure", action="store_true", help="Skip TLS verification (insecure)")
    p.add_argument("--kafka-sasl-user", default="", help="SASL username for Kafka")
    p.add_argument("--kafka-sasl-pass", default="", help="SASL password for Kafka")
    p.add_argument("--kafka-ca", default="certs/ca.cert.pem", help="CA certificate path")
    p.add_argument("--kafka-client-cert", default="", help="Client certificate path (optional)")
    p.add_argument("--kafka-client-key", default="", help="Client private key path (optional)")
    args = p.parse_args()

    client = clickhouse_connect.get_client(
        host=args.ch_host,
        port=args.ch_port,
        username=args.ch_user,
        password=args.ch_password,
    )
    ensure_schema(client)

    consumer_kwargs = dict(
        bootstrap_servers=args.kafka.split(","),
        group_id=args.group,
        enable_auto_commit=True,
        auto_offset_reset="earliest",
        value_deserializer=decode_metric,
    )
    if args.kafka_tls:
        import ssl as _ssl
        context = _ssl.create_default_context(cafile=args.kafka_ca)
        if args.kafka_tls_insecure:
            context.check_hostname = False
            context.verify_mode = _ssl.CERT_NONE
        if args.kafka_client_cert and args.kafka_client_key:
            context.load_cert_chain(certfile=args.kafka_client_cert, keyfile=args.kafka_client_key)
        consumer_kwargs.update({
            "security_protocol": "SSL",
            "ssl_context": context,
        })
    if args.kafka_sasl_user:
        consumer_kwargs.update({
            "security_protocol": "SASL_SSL" if args.kafka_tls else "SASL_PLAINTEXT",
            "sasl_mechanism": "PLAIN",
            "sasl_plain_username": args.kafka_sasl_user,
            "sasl_plain_password": args.kafka_sasl_pass,
        })

    consumer = KafkaConsumer(args.topic, **consumer_kwargs)

    stop = False

    def _stop(*_: Any) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    buffer: list[list[Any]] = []
    last_flush = time.monotonic()
    log.info("Consuming topic=%s group=%s", args.topic, args.group)

    try:
        while not stop:
            polled = consumer.poll(timeout_ms=500, max_records=500)
            if not polled:
                if buffer and (time.monotonic() - last_flush) >= args.flush_interval:
                    _flush(client, buffer)
                    buffer.clear()
                    last_flush = time.monotonic()
                continue
            for _tp, records in polled.items():
                for rec in records:
                    try:
                        buffer.append(row_from_payload(rec.value))
                    except (KeyError, ValueError, TypeError) as e:
                        log.warning("Bad record: %s err=%s", rec.value, e)
            if len(buffer) >= args.batch_size:
                _flush(client, buffer)
                buffer.clear()
                last_flush = time.monotonic()
            elif buffer and (time.monotonic() - last_flush) >= args.flush_interval:
                _flush(client, buffer)
                buffer.clear()
                last_flush = time.monotonic()
    except KafkaError as e:
        log.error("Kafka error: %s", e)
        sys.exit(1)
    finally:
        if buffer:
            _flush(client, buffer)
        consumer.close()
        log.info("Sink stopped")


def _flush(client: Any, rows: list[list[Any]]) -> None:
    if not rows:
        return
    with tracer.start_as_current_span("clickhouse-insert") as span:
        span.set_attribute("row_count", len(rows))
        client.insert(
            "network_telemetry.network_metrics",
            rows,
            column_names=[
                "ts",
                "src_ip",
                "dst_ip",
                "src_port",
                "dst_port",
                "protocol",
                "bytes",
                "packets",
            ],
        )
        log.info("Inserted %s rows into ClickHouse", len(rows))


if __name__ == "__main__":
    main()
