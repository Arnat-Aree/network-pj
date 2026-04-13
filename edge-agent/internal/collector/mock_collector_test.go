package collector

import (
	"net"
	"testing"
)

func TestGenerateMetricShape(t *testing.T) {
	m := Generate()
	if m.TS == "" {
		t.Fatal("timestamp should not be empty")
	}
	if net.ParseIP(m.SrcIP) == nil {
		t.Fatalf("invalid src ip: %s", m.SrcIP)
	}
	if net.ParseIP(m.DstIP) == nil {
		t.Fatalf("invalid dst ip: %s", m.DstIP)
	}
	if m.SrcPort < 1024 || m.SrcPort > 65024 {
		t.Fatalf("src port out of range: %d", m.SrcPort)
	}
	if m.Bytes < 64 {
		t.Fatalf("bytes below minimum: %d", m.Bytes)
	}
	if m.Packets < 1 {
		t.Fatalf("packets below minimum: %d", m.Packets)
	}
}
