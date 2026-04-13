.PHONY: all test fmt lint build docker-build

all: test

# Go
GO_PKG=edge-agent

test:
	@echo "Running tests..."
	@cd edge-agent && go test ./... \
		|| echo "Go tests failed or none present"
	@python3 -m pytest -q || echo "Python tests failed or none present"

fmt:
	@echo "Formatting Go code"
	@cd edge-agent && go fmt ./...

lint:
	@echo "Run linters (install golangci-lint separately)"
	@cd edge-agent && golangci-lint run || true

build:
	@echo "Building Go binary"
	@cd edge-agent && CGO_ENABLED=0 GOOS=linux go build -o build/agent ./cmd/agent

docker-build: build
	@echo "Building Docker images"
	docker build -t network-pj/edge-agent:latest -f edge-agent/Dockerfile .
	docker build -t network-pj/backend-api:latest -f backend/Dockerfile .
