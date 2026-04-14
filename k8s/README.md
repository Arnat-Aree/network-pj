Kubernetes deployment notes

1) Create TLS/SASL secrets (example):

kubectl create secret generic nti-secrets \
  --from-literal=CLICKHOUSE_PASSWORD="supersecret" \
  --from-literal=KAFKA_SASL_USER="kafka_user" \
  --from-literal=KAFKA_SASL_PASS="kafka_pass"

2) Apply manifests:

kubectl apply -f k8s/edge-agent-deployment.yaml
kubectl apply -f k8s/api-deployment.yaml

3) Prometheus:
 - Ensure Prometheus scrape config targets edge-agent `:9090/metrics` and API `/metrics`.
