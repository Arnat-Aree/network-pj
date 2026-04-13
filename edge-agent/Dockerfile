FROM golang:alpine AS builder
WORKDIR /src
COPY edge-agent/go.mod edge-agent/go.sum* ./
RUN go env -w GOPROXY=https://proxy.golang.org,direct
COPY edge-agent/ ./
RUN apk add --no-cache build-base git
RUN go mod tidy
RUN CGO_ENABLED=0 GOOS=linux go build -o /out/agent ./cmd/agent

FROM gcr.io/distroless/static-debian11
COPY --from=builder /out/agent /usr/local/bin/agent
USER 65532:65532
ENTRYPOINT ["/usr/local/bin/agent"]
