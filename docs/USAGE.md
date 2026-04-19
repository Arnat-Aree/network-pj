# 🖥️ Enterprise Operational Usage Guide

This manual is for Network Operations Center (NOC) operators and SREs to understand how to monitor, investigate, and analyze data using the NTI platform.

---

## 1. Visualizing Network Health (Grafana)

The primary interface for monitoring is **Grafana**. 
- **URL**: `http://localhost:3001`
- **Default Login**: `admin / admin`

### 📊 The NOC Dashboard
Located under `Dashboards > General > Network Telemetry (Hardcore Enterprise)`.

#### Key Panels Explained:
1. **Live Throughput (PPS/BPS)**: Real-time bandwidth usage. Spikes here might indicate DDoS or backup runs.
2. **Top Talkers (Source IPs)**: Ranking of top bandwidth-consuming endpoints. Powered by **ClickHouse Materialized Views** for instantaneous filtering over billions of rows.
3. **Latency Heatmap**: Shows the delay between data collection and database insertion (End-to-end pipeline latency).

---

## 2. Advanced Log Investigation (Loki)

When troubleshooting a specific event (e.g., "Why did Agent A crash?"), use **Loki**.

### 🔍 Explore Querying
Go to the **Explore** icon (compass) and select **Loki** as the datasource.

#### Useful Query Snippets:
| Objective | LogQL Query |
| :--- | :--- |
| **All Agent Logs** | `{container="network-pj-edge-agent-1"}` |
| **Filter Errors** | `{container="network-pj-edge-agent-1"} \|= "error" \|= "kafka"` |
| **Search by IP** | `{container="network-pj-kafka-sink-1"} \|~ "192.168.1.50"` |

> [!TIP]
> Click the **Live** button in the top right to stream logs in real-time like `tail -f`.

---

## 3. Distributed Tracing (Jaeger)

Use Jaeger to identify bottlenecks or message loss in the pipeline.
- **URL**: `http://localhost:16686`

### 🧭 Analyzing a Trace
1. Select **Service**: `edge-agent`.
2. Click **Find Traces**.
3. Select a trace with the operation `collect-and-publish`.

#### Detailed Span Breakdown:
- **`collect-metrics`**: Time taken to read from system interfaces.
- **`kafka-publish`**: Latency of the Avro serialization and Kafka broker handshake.
- **`clickhouse-insert`** (Linked Trace): Time taken for the Sink to batch-insert the data into ClickHouse.

---

## 4. API Consumption (FastAPI)

For custom integrations or script-based reporting, use the REST API.
- **Interactive Documentation**: `http://localhost:8000/docs` (Swagger UI)

### 🔑 Security (X-API-Key)
All requests MUST include the master key in the header. If missing, you will receive a `403 Forbidden`.

### 💻 cURL Examples

#### Get Current Top Talkers:
```bash
curl -H "X-API-Key: hardcore-production-key-2026" \
     "http://localhost:8000/api/v1/top-talkers?limit=10"
```

#### Get Bandwidth Stats (Last 60 mins):
```bash
curl -H "X-API-Key: hardcore-production-key-2026" \
     "http://localhost:8000/api/v1/bandwidth-per-minute?minutes=60"
```

### 📦 Response Schema (JSON)
```json
{
  "status": "success",
  "data": [
    {
      "src_ip": "192.168.1.10",
      "total_bytes": 5242880,
      "packet_count": 4500
    }
  ]
}
```

---

## 5. Maintenance Procedures

### 🧹 Clearing Old Data
ClickHouse handles retention via TTL policies, but you can manually truncate if needed:
```bash
# TRUNCATE ALL METRICS (CAUTION!)
docker exec network-pj-clickhouse-1 clickhouse-client -q "TRUNCATE TABLE network_telemetry.network_metrics"
```

### 🔄 Restarting the Pipeline
To refresh the agent configuration without stopping the database:
```bash
docker compose restart edge-agent
```
