package collector

import (
	"fmt"
	"math/rand"
	"time"
)

type Metric struct {
	TS       string `json:"ts" avro:"ts"`
	SrcIP    string `json:"src_ip" avro:"src_ip"`
	DstIP    string `json:"dst_ip" avro:"dst_ip"`
	SrcPort  int32  `json:"src_port" avro:"src_port"`
	DstPort  int32  `json:"dst_port" avro:"dst_port"`
	Protocol string `json:"protocol" avro:"protocol"`
	Bytes    int64  `json:"bytes" avro:"bytes"`
	Packets  int64  `json:"packets" avro:"packets"`
}

func Generate() Metric {
	protocols := []string{"TCP", "UDP", "ICMP"}
	srcA := rand.Intn(223)
	srcB := rand.Intn(255)
	dstA := rand.Intn(223)
	dstB := rand.Intn(255)
	return Metric{
		TS:       time.Now().UTC().Format(time.RFC3339Nano),
		SrcIP:    fmt.Sprintf("10.%d.%d.%d", srcA, srcB, rand.Intn(255)),
		DstIP:    fmt.Sprintf("172.%d.%d.%d", dstA, dstB, rand.Intn(255)),
		SrcPort:  int32(1024 + rand.Intn(64000)),
		DstPort:  int32([]uint32{22, 53, 80, 443, 8080}[rand.Intn(5)]),
		Protocol: protocols[rand.Intn(len(protocols))],
		Bytes:    int64(64 + rand.Intn(1_500_000)),
		Packets:  int64(1 + rand.Intn(10_000)),
	}
}
