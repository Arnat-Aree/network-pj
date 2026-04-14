# 🧪 Enterprise Network Telemetry - Test Plan

This document outlines the validation strategy for the Network Telemetry Intelligence (NTI) stack, ensuring reliability across data ingestion, storage, and API querying.

## 1. Unit Testing Strategy

### 🛰️ Edge Agent (Go)
Unit tests for the collection logic, ticker, and publishers.
- **Command**: `cd edge-agent && go test ./...`
- **Key Tests**:
    - `internal/collector`: Verifies random metric generation logic.
    - `internal/publisher`: Verifies JSON/Avro marshaling and Kafka client initialization.

### 🐍 Backend Services (Python)
Uses `pytest` for validating the API, Sink, and Codec logic.
- **Command**: `pytest backend/tests`
- **Modules Covered**:
    - `api.py`: Mocking ClickHouse to test FastAPI endpoint response structure.
    - `codec.py`: Testing Avro serialization/deserialization.
    - `kafka_clickhouse_sink.py`: Testing batching logic and data row formation.

---

## 2. Integration Testing (Pipeline Validation)

We use a "Black Box" approach to verify end-to-end data flow:

1. **Schema Check**: Ensure `schema-registry` has the correct `network-telemetry-avro-value` schema.
   - `curl http://localhost:8081/subjects/network-telemetry-avro-value/versions/latest`
2. **Data Flow**:
   - Run `mock-producer` to inject 1000 messages.
   - Verify `network_metrics` table count increasing in ClickHouse.
   - `docker exec -it network-pj-clickhouse-1 clickhouse-client -q "SELECT count() FROM network_telemetry.network_metrics"`
3. **Aggregation Check**:
   - Verify Materialized Views (`top_talkers`, `bandwidth_minutely`) contain aggregated data.

---

## 3. Security & Access Testing

### API Key Auth
Verify the `X-API-Key` middleware in FastAPI.
- **Valid Key**: `curl -I -H "X-API-Key: <key>" http://localhost:8000/api/v1/top-talkers` -> `200 OK`
- **Invalid Key**: `curl -I -H "X-API-Key: wrong" http://localhost:8000/api/v1/top-talkers` -> `403 Forbidden`
- **Missing Key**: `curl -I http://localhost:8000/api/v1/top-talkers` -> `403 Forbidden`

### Kafka TLS/SASL
Verify using `kafka-console-consumer` with `client.properties`.

---

## 4. Observability Validation

Visual check of the "LGTM" Stack:
- **Loki**: Check if logs contain `"level":"info"`.
- **Prometheus**: Check `nti_http_requests_total` metric.
- **Jaeger**: Verify spans `collect-and-publish` -> `kafka-publish` -> `clickhouse-insert` are linked in a single trace.
