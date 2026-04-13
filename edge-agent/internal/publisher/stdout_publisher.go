package publisher

import (
	"context"
	"encoding/json"
	"fmt"

	"network-pj/edge-agent/internal/collector"
)

type StdoutPublisher struct{}

func NewStdoutPublisher() *StdoutPublisher {
	return &StdoutPublisher{}
}

func (p *StdoutPublisher) Publish(ctx context.Context, topic string, m collector.Metric) error {
	b, err := json.Marshal(m)
	if err != nil {
		return err
	}
	fmt.Printf("[edge-agent] topic=%s payload=%s\n", topic, string(b))
	return nil
}

func (p *StdoutPublisher) Close() error { return nil }
