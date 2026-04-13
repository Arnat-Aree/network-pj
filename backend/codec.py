import io
import json
import os
import struct
import requests
from pathlib import Path
from typing import Any

from fastavro import parse_schema, schemaless_reader, schemaless_writer

REGISTRY_URL = os.getenv("NTA_REGISTRY_URL", "http://schema-registry:8081")
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "network_metric.avsc"
LOCAL_SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
SCHEMA = parse_schema(LOCAL_SCHEMA)

# Cache for schema ID
_SCHEMA_ID: int | None = None


def get_schema_id() -> int:
    global _SCHEMA_ID
    if _SCHEMA_ID is not None:
        return _SCHEMA_ID

    # Register/Get ID from Schema Registry
    subject = "network-telemetry-avro"
    try:
        res = requests.post(
            f"{REGISTRY_URL}/subjects/{subject}/versions",
            json={"schema": json.dumps(LOCAL_SCHEMA)},
            timeout=5
        )
        res.raise_for_status()
        _SCHEMA_ID = res.json()["id"]
        return _SCHEMA_ID
    except Exception as e:
        # Fallback for local testing if registry is down
        print(f"Warning: Could not connect to Schema Registry: {e}")
        return 0


def encode_metric(record: dict[str, Any]) -> bytes:
    schema_id = get_schema_id()
    buf = io.BytesIO()
    # Confluent Magic Byte (0) + 4-byte Schema ID
    buf.write(struct.pack(">bI", 0, schema_id))
    schemaless_writer(buf, SCHEMA, record)
    return buf.getvalue()


def decode_metric(payload: bytes) -> dict[str, Any]:
    # Skip magic byte and schema ID (5 bytes)
    # In a full enterprise app, we'd use the ID to fetch the schema from a cache/registry
    buf = io.BytesIO(payload)
    header = buf.read(5)
    if len(header) < 5 or header[0] != 0:
        # Fallback for plain Avro
        buf.seek(0)
    return schemaless_reader(buf, SCHEMA)
