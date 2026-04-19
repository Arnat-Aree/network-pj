# Network Telemetry Intelligence (NTI) — AI Architect Plan

เอกสารนี้เป็น **Blueprint ระดับ Enterprise Architecture** สำหรับ Intelligent Network Telemetry Intelligence ที่ใช้เป็น Context เริ่มต้นให้ AI (เช่น Claude / GPT) คิดแบบ System Architect — เหมาะสำหรับโปรไฟล์ระดับ **Senior / Network Automation Engineer**

---

> [!NOTE]
> **PROJECT STATUS: ✅ COMPLETED & PRODUCTION READY**
> All components implemented, CI/CD pipeline green, Docker Compose integration tested, and Observability stack validated end-to-end. (Verified 2026-04-19)

### Verified State Summary (As of 2026-04-19)
- **CI/CD Pipeline**: ✅ **All Green** — GitHub Actions CI #25 / CD #25 both passed.
- **Python Tests**: ✅ **9/9 Passed** — All backend unit tests (API, Sink, Codec, Mock Producer).
- **Go Tests**: ✅ **Passed on CI** — Go 1.23 on GitHub Actions.
- **Docker Compose**: ✅ **13/13 containers healthy** — Full stack integration test passed.
- **API Endpoints**: ✅ **Real data flowing** — Top Talkers & Bandwidth API returning live metrics.
- **Tracing**: ✅ Jaeger (port 16686) — Distributed Tracing with OpenTelemetry.
- **Logging**: ✅ Loki (port 3100) + Promtail — Centralized Structured Logging.
- **Metrics**: ✅ Prometheus (port 9090) — System metrics collection.
- **Dashboard**: ✅ Grafana (port 3001) — "Network Telemetry (Hardcore Enterprise)" dashboard provisioned.
- **Security**: ✅ API Key Auth (`X-API-Key`) + Kafka TLS/SASL ready.
- **Data Governance**: ✅ Schema Registry + Avro wire format validated in CI.
- **Documentation**: ✅ README, SETUP.md, USAGE.md, PRODUCTION_GUIDE.md, TEST_PLAN.md.

---

## The Enterprise Architecture (The “Big Data” Network Stack)

ออกแบบเป็น **Event-Driven Architecture** แบ่งเป็น **4 Layers**:

### 1. Collection Layer (Edge Agents)

| หัวข้อ | รายละเอียด |
|--------|-------------|
| **เทคโนโลยี** | Golang + eBPF (Extended Berkeley Packet Filter) หรือ Rust |
| **ทำไมใช้** | eBPF ทำงานในระดับ OS Kernel (Zero-copy) ดักจับและวิเคราะห์ Packet ได้ความเร็วระดับ **10–100 Gbps** โดยแทบไม่กิน CPU |

### 2. Ingestion & Buffering Layer (Message Broker)

| หัวข้อ | รายละเอียด |
|--------|-------------|
| **เทคโนโลยี** | Apache Kafka หรือ Redpanda |
| **ทำไมใช้** | เมื่อเกิด Traffic Spikes (เช่น DDoS) ระบบไม่ล่ม — Broker รับสถิติจาก Agent เก็บใน Queue ชั่วคราว |

### 3. Storage & Analytics Layer (Database)

| หัวข้อ | รายละเอียด |
|--------|-------------|
| **เทคโนโลยี** | ClickHouse (Columnar) หรือ TimescaleDB |
| **ทำไมใช้** | Insert ระดับล้าน record/วินาที และ Query ย้อนหลังระดับ Terabyte ได้ในหลักมิลลิวินาที |

### 4. Presentation & API Layer

| หัวข้อ | รายละเอียด |
|--------|-------------|
| **Backend** | FastAPI (Python) หรือ Go (Gin) + gRPC / GraphQL |
| **Frontend** | Next.js (React) + Apache ECharts — หรือ Grafana เพื่อมาตรฐาน Enterprise |

### Infrastructure & Deployment

Docker, Kubernetes (K8s), Terraform

---

## 1. Project Vision & Scope

สร้างระบบ **Network Telemetry และ Traffic Analysis** ระดับ Enterprise-Grade ที่รองรับ **High-Throughput (10Gbps+)**, **Scalability** และ **Real-time Anomaly Detection**

---

## 2. Enterprise Tech Stack

- **Edge Node (Packet Capture):** Golang + `cilium/ebpf` — eBPF กรองข้อมูลจาก Kernel โดยตรงเพื่อ Performance สูงสุด
- **Message Broker:** Apache Kafka (Dockerized) สำหรับ High Ingestion Rate
- **Time-Series / OLAP Database:** ClickHouse — Schema สำหรับ Time-series data
- **Backend API:** Python (FastAPI) หรือ Golang (Fiber)
- **Frontend / Visualization:** Next.js + Grafana Dashboard integration
- **Infrastructure:** Kubernetes (Minikube / K3s สำหรับ Local), Helm Charts, Docker Compose

---

## 3. System Architecture & Data Flow

```
[Network Interface] → (eBPF Program) → [Golang Agent] → (gRPC/Protobuf)
    → [Kafka Topic: network-telemetry] → [ClickHouse Consumer/Sink]
    → [FastAPI] → [Next.js / Grafana]
```

---

## 4. Strict Enterprise Guidelines

- **Performance First:** ห้ามดึง Full Packet Payload ข้าม network — Edge Agent ต้อง **Aggregate** (เช่น สรุปสถิติทุก 1 วินาที) ก่อนส่งเข้า Kafka
- **Data Serialization:** Agent ↔ Kafka ใช้ **Protocol Buffers (Protobuf)** หรือ **Avro** เพื่อลดขนาดข้อมูล
- **Fault Tolerance:** ทุกบริการมี **Health Check** และพร้อม **Auto-restart** หากล่ม
- **Security:** API มี **Authentication (JWT / OAuth2)** — การเชื่อมต่อระหว่าง Node รองรับ **TLS**

---

## 5. Execution Roadmap (GitHub Issues)

### Epic 1: High-Performance Edge Agent

- **Issue 1.1:** Setup โปรเจกต์ Golang และเขียน eBPF program (C) ดักจับ **XDP (eXpress Data Path)** หรือ **TC (Traffic Control)** hooks
- **Issue 1.2:** Go logic อ่านจาก eBPF Map — นับ Bytes/Packets แยกตาม **5-Tuple** (Src IP, Dst IP, Src Port, Dst Port, Protocol)
- **Issue 1.3:** Protobuf schema สำหรับ `NetworkMetric` และระบบ Publish เข้า Apache Kafka

### Epic 2: Data Pipeline & Storage

- **Issue 2.1:** Setup Kafka + Zookeeper / KRaft ผ่าน Docker Compose
- **Issue 2.2:** Setup ClickHouse — Table Schema แบบ `MergeTree` พาร์ทิชันตามวันและเวลา
- **Issue 2.3:** Data Consumer (Kafka Connect หรือ Python/Go) — ดึงจาก Kafka ลง ClickHouse แบบ **Batch Insert**

### Epic 3: API & Visualization

- **Issue 3.1:** FastAPI service เชื่อม ClickHouse — Query สถิติ (Top Talkers, Bandwidth per second)
- **Issue 3.2:** Grafana เชื่อม ClickHouse เป็น Data Source + Dashboard — หรือ Custom UI ด้วย Next.js + ECharts

---

## 6. คำแนะนำการดำเนินโปรเจกต์ (สเกลใหญ่)

โปรเจกต์นี้ใหญ่และลึก — แนะนำทำ **ทีละ Epic** ตามลำดับ:

### เริ่มจาก “The Heart” (Data Pipeline)

1. ตั้ง **Docker Compose** ให้มี **Kafka + ClickHouse** รันได้ก่อน
2. เขียน **Python script** จำลองข้อมูล (Mock Data) เข้า Kafka เพื่อตรวจว่าไหลลง Database ถูกต้อง

### ต่อด้วย “The Brain” (eBPF Agent)

- ส่วนที่ยากและโดดเด่นบน Resume — ศึกษา **eBPF** (Cloud Native / Security) ใช้ Golang (`cilium/ebpf`) ฝัง logic ใน Linux Kernel

### ปิดท้ายด้วย “The Face” (Dashboard)

- ระดับ Enterprise มักใช้ **Grafana** เชื่อม ClickHouse แล้วลาก Dashboard — หรือถ้าต้องการโชว์ Frontend ค่อยทำ **Next.js** ดึง API

---

## 7. วิธีใช้เอกสารนี้กับ AI

- วาง `AI_MASTER_PLAN.md` ใน Repo หรือแนบเป็น Context ตอนเริ่ม Session
- ระบุ Epic / Issue ที่กำลังทำ เพื่อให้คำตอบและโค้ดสอดคล้องกับแนว Enterprise ด้านบน
