package publisher

import (
	"bytes"
	"context"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"strings"
	"time"

	"github.com/hamba/avro/v2"
	"github.com/segmentio/kafka-go"
	"go.opentelemetry.io/otel"
	"network-pj/edge-agent/internal/collector"
)

type KafkaPublisher struct {
	writer     *kafka.Writer
	schema     avro.Schema
	schemaID   uint32
	registryURL string
}

func NewKafkaPublisher(brokers string, tlsEnabled bool, tlsInsecure bool, saslUser, saslPass string, registryURL string) *KafkaPublisher {
	addrs := strings.Split(brokers, ",")
	
	// Hardcore Enterprise logic: Load Avro schema from central location or embed it
	// For this demo, we assume the schema is standard. 
	// In a real app, we'd load this from a .avsc file or the Registry.
	schemaStr := `{
		"type": "record",
		"name": "NetworkMetric",
		"fields": [
			{"name": "ts", "type": "string"},
			{"name": "src_ip", "type": "string"},
			{"name": "dst_ip", "type": "string"},
			{"name": "src_port", "type": "int"},
			{"name": "dst_port", "type": "int"},
			{"name": "protocol", "type": "string"},
			{"name": "bytes", "type": "long"},
			{"name": "packets", "type": "long"}
		]
	}`
	sch, _ := avro.Parse(schemaStr)

	p := &KafkaPublisher{
		writer: &kafka.Writer{
			Addr:         kafka.TCP(addrs...),
			Balancer:     &kafka.LeastBytes{},
			RequiredAcks: kafka.RequireOne,
			Async:        true,
		},
		schema:      sch,
		registryURL: registryURL,
	}

	// Fetch Schema ID from Registry (Enterprise Pattern)
	p.initSchemaID(schemaStr)

	return p
}

func (p *KafkaPublisher) initSchemaID(schemaStr string) {
	if p.registryURL == "" {
		p.registryURL = "http://schema-registry:8081"
	}
	subject := "network-telemetry-avro-value"
	url := fmt.Sprintf("%s/subjects/%s/versions", p.registryURL, subject)
	
	body, _ := json.Marshal(map[string]string{"schema": schemaStr})
	resp, err := http.Post(url, "application/vnd.schemaregistry.v1+json", bytes.NewBuffer(body))
	if err != nil {
		slog.Warn("failed to connect to schema registry, using default ID 1", "err", err)
		p.schemaID = 1
		return
	}
	defer resp.Body.Close()

	var result struct {
		ID uint32 `json:"id"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		p.schemaID = 1
		return
	}
	p.schemaID = result.ID
	slog.Info("schema registered", "subject", subject, "id", p.schemaID)
}

func (p *KafkaPublisher) Publish(ctx context.Context, topic string, m collector.Metric) error {
	ctx, span := otel.Tracer("edge-agent").Start(ctx, "kafka-publish")
	defer span.End()

	// Encode to Avro
	data, err := avro.Marshal(p.schema, m)
	if err != nil {
		return fmt.Errorf("avro marshal error: %w", err)
	}

	// Confluent Wire Format: [Magic Byte 0] [4-byte Schema ID] [Avro Payload]
	payload := make([]byte, 5+len(data))
	payload[0] = 0
	binary.BigEndian.PutUint32(payload[1:5], p.schemaID)
	copy(payload[5:], data)

	msg := kafka.Message{
		Topic: topic,
		Value: payload,
	}
	
	writeCtx, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()

	return p.writer.WriteMessages(writeCtx, msg)
}

func (p *KafkaPublisher) Close() error {
	return p.writer.Close()
}
