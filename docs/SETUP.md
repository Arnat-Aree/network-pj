# 📘 Enterprise Setup & Deployment Guide

This guide provides a comprehensive, step-by-step procedure for deploying the Network Telemetry Intelligence (NTI) stack in a production-ready environment.

---

## 1. Prerequisites & System Requirements

### 💻 Hardware Specifications
For a stable enterprise environment, ensure your host meets these minimums:
- **CPU**: 4 Cores (Dedicated)
- **RAM**: 8 GB (16 GB Recommended for large ClickHouse buffers)
- **Disk**: 50 GB SSD (NVMe preferred for high IOPS ClickHouse operations)
- **OS**: Linux (Ubuntu 22.04+), macOS (Monterey+), or Windows with WSL2

### 🛠️ Software Dependencies
- **Docker**: Engine 24.0+
- **Docker Compose**: V2 2.20+
- **OpenSSL**: For certificate generation
- **Java Runtime (JRE)**: Required for the `keytool` command used in Kafka keystore creation.

---

## 2. Security & Certificate Management

The NTI stack uses a **Defense-in-Depth** security model. In a production environment, you must initialize the SSL/TLS certificates before starting the services.

### 🔐 Certificate Hierarchy
The system uses a Private Certificate Authority (CA) to sign all service certificates:
- **`ca.cert.pem`**: The root of trust. All services and clients must trust this.
- **`server.cert.pem`**: Used by the Kafka brokers.
- **`client.cert.pem`**: Used by producers (Edge Agent) and consumers (Kafka Sink).
- **`keystore.jks` / `truststore.jks`**: Java-format stores used by the Confluent Kafka container.

### ⚡ Generating Certificates
Navigate to the `certs` directory and execute the generation script:
```bash
cd certs
chmod +x generate-certs.sh
./generate-certs.sh
cd ..
```
> [!WARNING]
> This script will generate a file named `kafka_password.txt`. This contains the JKS password (default: `changeit`). Ensure this file is secured and not committed to Version Control.

---

## 3. Environment Configuration (`.env`)

Clone `.env.sample` to `.env` and adjust the variables based on your network topology.

| Variable | Default Value | Technical Impact |
| :--- | :--- | :--- |
| `NTI_CH_PASSWORD` | `NTI_Secure_2026` | Root password for ClickHouse. |
| `NTI_API_KEY` | `hardcore-production-key-2026` | Master key for the FastAPI analytics layer. |
| `NTI_KAFKA_TLS` | `true` | When true, services will use port 9093 with SSL/TLS. |
| `NTI_EDGE_INTERVAL_SEC` | `1` | Collection frequency. Lowering this increases load on Kafka/CH. |
| `ENVIRONMENT` | `development` | Switches logging levels and OTel debugging. |

---

## 4. Booting the Enterprise Stack

We use a specific startup sequence to ensure that the Database and Message Broker are healthy before the application layer starts.

### 🆙 Command
```bash
docker compose up -d --build
```

### 🩺 Healthcheck Logic
The `docker-compose.yml` includes sophisticated healthchecks:
1. **Kafka**: Uses `kafka-broker-api-versions` to verify the broker is actually ready to accept connections.
2. **ClickHouse**: Periodic HTTP pings to `/ping` to ensure the storage engine is mounted.
3. **Application Loop**: The `edge-agent` and `kafka-sink` will automatically wait (via `depends_on: condition: service_healthy`) for the infrastructure to stabilize.

---

## 5. Troubleshooting FAQ

### ❌ Kafka Connection Denied
- **Symptoms**: `edge-agent` logs show `connection refused to localhost:9092`.
- **Fix**: Check if `NTI_KAFKA_BROKERS` is set correctly. Inside Docker, it should be `kafka:9092`. Outside Docker, use `localhost:9092`.

### ❌ ClickHouse Write Lag
- **Symptoms**: `kafka-sink` logs show `Batch insert timeout`.
- **Fix**: Increase the `max_memory_usage` and `max_insert_block_size` in ClickHouse config, or increase Docker's RAM allocation (at least 2GB for ClickHouse).

### ❌ Traces Missing in Jaeger
- **Symptoms**: No services appear in Jaeger Service dropdown.
- **Fix**: Verify `OTEL_COLLECTOR` is set to `jaeger:4317` (gRPC). Ensure port 4317 is open and mapped in the jaeger container.

---

## 6. Capacity Planning (Estimation)

| Data Load | Storage / Day | CPU Impact |
| :--- | :--- | :--- |
| **100 pkts/sec** | ~500 MB | Negligible |
| **10k pkts/sec** | ~5 GB | 1-2 Cores (CH Aggregations) |
| **1M pkts/sec** | ~500 GB | Cluster Needed |

> [!TIP]
> Use the **Materialized Views** feature to store data at 1-minute granularity for long-term retention, while keeping raw metrics only for 7-14 days.
