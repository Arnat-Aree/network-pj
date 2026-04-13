package publisher

import (
	"bytes"
	"context"
	"io"
	"os"
	"strings"
	"testing"

	"network-pj/edge-agent/internal/collector"
)

func TestPublishWritesExpectedLine(t *testing.T) {
	p := NewStdoutPublisher()
	m := collector.Metric{
		TS:       "2026-04-10T00:00:00Z",
		SrcIP:    "10.0.0.1",
		DstIP:    "172.16.0.1",
		SrcPort:  1234,
		DstPort:  443,
		Protocol: "TCP",
		Bytes:    100,
		Packets:  2,
	}

	oldStdout := os.Stdout
	r, w, err := os.Pipe()
	if err != nil {
		t.Fatalf("pipe failed: %v", err)
	}
	os.Stdout = w

	pubErr := p.Publish(context.Background(), "topic-test", m)
	_ = w.Close()
	os.Stdout = oldStdout
	if pubErr != nil {
		t.Fatalf("publish failed: %v", pubErr)
	}

	var buf bytes.Buffer
	_, _ = io.Copy(&buf, r)
	out := buf.String()
	if !strings.Contains(out, "topic=topic-test") {
		t.Fatalf("missing topic in output: %s", out)
	}
	if !strings.Contains(out, "\"src_ip\":\"10.0.0.1\"") {
		t.Fatalf("missing payload json in output: %s", out)
	}
}
