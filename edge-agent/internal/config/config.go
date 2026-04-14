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
		KafkaBrokers: getenv("NTI_KAFKA_BROKERS", "localhost:9092"),
		KafkaTopic:   getenv("NTI_KAFKA_TOPIC", "network-telemetry-avro"),
		IntervalSec:  getenv("NTI_EDGE_INTERVAL_SEC", "1"),
		Publisher:    getenv("NTI_PUBLISHER", "stdout"),
	KafkaTLS:         getenv("NTI_KAFKA_TLS", "false"),
	KafkaTLSInsecure: getenv("NTI_KAFKA_TLS_INSECURE", "false"),
	KafkaSASLUser:    getenv("NTI_KAFKA_SASL_USER", ""),
	KafkaSASLPass:    getenv("NTI_KAFKA_SASL_PASS", ""),
	}
}

func getenv(k, fallback string) string {
	v := os.Getenv(k)
	if v == "" {
		return fallback
	}
	return v
}
