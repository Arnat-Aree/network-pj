# Security Policy

This repository follows basic security hygiene:

- Do not commit secrets. Use `.env.production.sample` as template.
- Use image scanning (Trivy) in CI and fail on high/critical vulnerabilities.
- Use TLS for Kafka and ClickHouse in production.
- Use Schema Registry to prevent incompatible schema changes.

If you find a vulnerability, please open an issue or contact the repo owner.
