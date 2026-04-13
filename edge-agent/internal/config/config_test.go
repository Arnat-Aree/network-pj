package config

import "testing"

func TestLoadDefaults(t *testing.T) {
	t.Setenv("NTA_KAFKA_BROKERS", "")
	t.Setenv("NTA_KAFKA_TOPIC", "")
	t.Setenv("NTA_EDGE_INTERVAL_SEC", "")

	cfg := Load()
	if cfg.KafkaBrokers != "localhost:9092" {
		t.Fatalf("unexpected default broker: %s", cfg.KafkaBrokers)
	}
	if cfg.KafkaTopic != "network-telemetry-avro" {
		t.Fatalf("unexpected default topic: %s", cfg.KafkaTopic)
	}
	if cfg.IntervalSec != "1" {
		t.Fatalf("unexpected default interval: %s", cfg.IntervalSec)
	}
}

func TestLoadOverrides(t *testing.T) {
	t.Setenv("NTA_KAFKA_BROKERS", "kafka:9092")
	t.Setenv("NTA_KAFKA_TOPIC", "topic-a")
	t.Setenv("NTA_EDGE_INTERVAL_SEC", "5")

	cfg := Load()
	if cfg.KafkaBrokers != "kafka:9092" || cfg.KafkaTopic != "topic-a" || cfg.IntervalSec != "5" {
		t.Fatalf("env override not applied: %+v", cfg)
	}
}
