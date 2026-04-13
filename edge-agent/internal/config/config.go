package config

import "os"

type Config struct {
	KafkaBrokers string
	KafkaTopic   string
	IntervalSec  string
	Publisher    string
	KafkaTLS         string
	KafkaTLSInsecure string
	KafkaSASLUser    string
	KafkaSASLPass    string
}

func Load() Config {
	return Config{
		KafkaBrokers: getenv("NTA_KAFKA_BROKERS", "localhost:9092"),
		KafkaTopic:   getenv("NTA_KAFKA_TOPIC", "network-telemetry-avro"),
		IntervalSec:  getenv("NTA_EDGE_INTERVAL_SEC", "1"),
		Publisher:    getenv("NTA_PUBLISHER", "stdout"),
	KafkaTLS:         getenv("NTA_KAFKA_TLS", "false"),
	KafkaTLSInsecure: getenv("NTA_KAFKA_TLS_INSECURE", "false"),
	KafkaSASLUser:    getenv("NTA_KAFKA_SASL_USER", ""),
	KafkaSASLPass:    getenv("NTA_KAFKA_SASL_PASS", ""),
	}
}

func getenv(k, fallback string) string {
	v := os.Getenv(k)
	if v == "" {
		return fallback
	}
	return v
}
