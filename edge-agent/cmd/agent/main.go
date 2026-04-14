package main

import (
	"context"
	"log/slog"
	"math/rand"
	"net/http"
	"os"
	"strconv"
	"time"

	"network-pj/edge-agent/internal/collector"
	"network-pj/edge-agent/internal/config"
	"network-pj/edge-agent/internal/publisher"

	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.17.0"
	"go.opentelemetry.io/otel/trace"
)

var tracer trace.Tracer

func main() {
	// Enterprise Structured Logging
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	slog.SetDefault(logger)

	// Initialize OpenTelemetry
	tp, err := initTracer()
	if err != nil {
		slog.Error("failed to initialize tracer", "err", err)
	} else {
		defer func() {
			if err := tp.Shutdown(context.Background()); err != nil {
				slog.Error("failed to shutdown tracer", "err", err)
			}
		}()
	}
	tracer = otel.Tracer("edge-agent")

	cfg := config.Load()
	intervalSec, _ := strconv.Atoi(cfg.IntervalSec)
	if intervalSec < 1 {
		intervalSec = 1
	}

	rand.Seed(time.Now().UnixNano())
	var pub interface {
		Publish(context.Context, string, collector.Metric) error
		Close() error
	}

	if cfg.Publisher == "kafka" {
		tlsEnabled := cfg.KafkaTLS == "true"
		tlsInsecure := cfg.KafkaTLSInsecure == "true"
		// Registry URL from env or default
		registryURL := os.Getenv("NTI_REGISTRY_URL")
		kp := publisher.NewKafkaPublisher(cfg.KafkaBrokers, tlsEnabled, tlsInsecure, cfg.KafkaSASLUser, cfg.KafkaSASLPass, registryURL)
		pub = kp
		defer kp.Close()
	} else {
		sp := publisher.NewStdoutPublisher()
		pub = sp
		defer sp.Close()
	}

	// Metrics endpoint
	go func() {
		http.Handle("/metrics", promhttp.Handler())
		slog.Info("prometheus metrics available", "port", 9091)
		if err := http.ListenAndServe(":9091", nil); err != nil {
			slog.Error("metrics server error", "err", err)
		}
	}()

	ticker := time.NewTicker(time.Duration(intervalSec) * time.Second)
	defer ticker.Stop()

	slog.Info("edge-agent started", "brokers", cfg.KafkaBrokers, "topic", cfg.KafkaTopic, "interval", intervalSec)

	for range ticker.C {
		ctx, span := tracer.Start(context.Background(), "collect-and-publish")
		m := collector.Generate()
		if err := pub.Publish(ctx, cfg.KafkaTopic, m); err != nil {
			slog.Error("publish error", "err", err)
		}
		span.End()
	}
}

func initTracer() (*sdktrace.TracerProvider, error) {
	ctx := context.Background()

	endpoint := os.Getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
	if endpoint == "" {
		endpoint = "jaeger:4317"
	}

	exporter, err := otlptracegrpc.New(ctx,
		otlptracegrpc.WithInsecure(),
		otlptracegrpc.WithEndpoint(endpoint),
	)
	if err != nil {
		return nil, err
	}

	res, err := resource.New(ctx,
		resource.WithAttributes(
			semconv.ServiceNameKey.String("edge-agent"),
		),
	)
	if err != nil {
		return nil, err
	}

	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(res),
	)
	otel.SetTracerProvider(tp)
	return tp, nil
}
