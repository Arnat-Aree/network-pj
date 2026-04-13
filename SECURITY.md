# 🛡️ Enterprise Security Policy

This document defines the security standards, vulnerability reporting procedures, and the response policy for the Network Telemetry Analyzer (NTA) project.

---

## 1. Supported Versions

We provide security updates for the following versions of NTA:

| Version | Status | Security Support |
| :--- | :--- | :--- |
| **7.0.x (Current)** | ✨ Active | Full Support |
| 6.x.y | 🛠️ Maintenance | Critical Only (Ends 2026-12) |
| < 6.0 | 🛑 End-of-Life | None |

---

## 2. Reporting a Vulnerability

We take the security of our enterprise telemetry pipeline seriously. If you believe you have found a security vulnerability in NTA, please follow the process below:

1.  **Do NOT open a public GitHub Issue**.
2.  Submit a detailed report to the **Private Security Channel** or email the repository owner directly.
3.  Include a brief description, steps to reproduce, and any potential impact.

### 🕙 Response Timeline
- **Acknowledgement**: Within 24 hours.
- **Initial Evaluation**: Within 3 business days.
- **Fix/Patch Disclosure**: Dependent on complexity (Target: < 14 days).

---

## 3. Responsible Disclosure Policy

- **Give us time**: Do not disclose the vulnerability to the public or any third party until we have had a reasonable amount of time to fix it.
- **Do no harm**: Avoid actions that could impact user data or system availability during your research.
- **No Ransom**: This project does not currently operate a bug bounty program. We appreciate ethical contributions.

---

## 4. Default Security Baseline

The following architectural decisions are baked into the NTA stack:

- **Auth-by-Default**: Every API endpoint is protected by `X-API-Key` middleware.
- **Wire Encryption**: Kafka traffic is encrypted via **SSL/TLS**.
- **Supply Chain Safety**: All Docker images undergo **Trivy Vulnerability Scanning** in the CI pipeline.
- **Schema Safety**: Avro Schema Enforcement prevents data poisoning at the ingestion layer.

---

## 5. Security Checklist (Production)

- [ ] Change the default `NTA_API_KEY` in your `.env`.
- [ ] Rotate Certs/JKS passwords every 90 days (See `docs/SETUP.md`).
- [ ] Ensure ClickHouse is running in a private VPC subnet.
- [ ] Enable SASL/SCRAM for Kafka client authentication.
