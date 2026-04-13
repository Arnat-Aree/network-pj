# Production Deployment Guide

This document outlines minimum requirements and steps to move the project from lab to production.

1) Secrets management
  - Use a secrets store (HashiCorp Vault, AWS Secrets Manager, or Kubernetes Secrets).
  - Do NOT store credentials in git. Use `.env.production` in CI/CD only as transient artifact.

2) Kafka security
  - Use TLS on broker listeners (9093) and require client authentication where possible.
  - Configure SASL (SCRAM/PLAIN) for producer/consumer authentication.
  - Provision client certs or SASL credentials via secrets store.

3) Schema Registry
  - Run a schema registry (Confluent Schema Registry or Apicurio) and register Avro/Protobuf schemas.
  - Add CI job to validate schema compatibility on PRs.

  Local dev (self-signed) guidance
  - For development you can generate a self-signed CA and certs using `certs/generate-certs.sh`.
  - The generated files are placed in `certs/` (this path is gitignored). Use the CA certificate to trust the broker in your local environment.
  - Example: configure Kafka broker to use `server.cert.pem`/`server.key.pem` and point clients to `ca.cert.pem` (or set `ssl_check_hostname=false` for quick local testing).


4) Observability
  - Enable Prometheus scraping for metrics endpoints (`:9091/metrics` for agent, `/metrics` for API).
  - Centralized Logging: Forward all container logs to **Loki** with a defined retention policy (currently 7 days).
  - Add OpenTelemetry tracing (Jaeger) and propagate trace IDs across the pipeline.

5) Deployment
  - Build and sign container images. Scan with Trivy and fail on critical vulns.
  - Deploy to Kubernetes using Helm charts with values for resources, replicas, and probes.
  - Use HorizontalPodAutoscaler (HPA) for the API and Sink.
  - Performance: Use ClickHouse **Materialized Views** to shift high-CPU aggregations from query-time to ingestion-time.

6) Network & Hardening
  - Run in private networks/VPC. Use network policies for k8s.
  - Enforce RBAC, PodSecurityPolicy / PSP alternatives.

7) Testing & Validation
  - Add performance tests for Kafka throughput and ClickHouse inserts.
  - Add chaos testing: broker failure, network partition, ClickHouse node failure.

Checklist (Implemented in this Repository):
  - [x] Secrets: Managed via .env (ready for Vault/K8s Secrets mapping)
  - [x] Kafka Security: TLS (Port 9093) and **SASL/SSL** ready
  - [x] API Security: **API Key Header Auth** implemented
  - [x] Schema Registry: Integrated into both Go & Python (Port 8081)
  - [x] Observability: Prometheus + Jaeger + **Loki (7-day logs)**
  - [x] Data Performance: **Materialized Views** for high-speed dashboards
  - [x] Container Hardening: All images run as `nonroot`
  - [x] DevOps: Helm charts + K8s manifests baseline provided
  - [x] Scalability: Structure ready for GitOps and HPA
