#!/usr/bin/env python3
"""Publish mock aggregated network metrics to Kafka using Avro binary records."""

from __future__ import annotations

import argparse
import random
import socket
import struct
import time
from datetime import datetime, timezone
import ssl

from kafka import KafkaProducer
from codec import encode_metric


def random_ipv4(rng: random.Random) -> str:
    return socket.inet_ntoa(struct.pack(">I", rng.randint(0x0A000000, 0xDEFFFFFF)))


def main() -> None:
    p = argparse.ArgumentParser(description="Mock network-telemetry producer")
    p.add_argument(
        "--bootstrap",
        default="localhost:9092",
        help="Kafka bootstrap servers",
    )
    p.add_argument("--tls", action="store_true", help="Enable TLS")
    p.add_argument("--ca", default="certs/ca.cert.pem", help="CA certificate path")
    p.add_argument("--topic", default="network-telemetry-avro", help="Kafka topic")
    p.add_argument("--count", type=int, default=50, help="Messages to send (0 = infinite)")
    p.add_argument("--interval", type=float, default=0.2, help="Seconds between messages")
    args = p.parse_args()

    rng = random.Random()
    producer_kwargs = dict(
        bootstrap_servers=args.bootstrap.split(","),
        value_serializer=encode_metric,
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        acks="all",
        retries=3,
    )
    if args.tls:
        context = ssl.create_default_context(cafile=args.ca)
        producer_kwargs.update({
            "security_protocol": "SSL",
            "ssl_context": context,
        })

    producer = KafkaProducer(**producer_kwargs)

    protocols = ("TCP", "UDP", "ICMP")
    n = 0
    try:
        while args.count == 0 or n < args.count:
            now = datetime.now(timezone.utc)
            src = random_ipv4(rng)
            dst = random_ipv4(rng)
            if src == dst:
                continue
            payload = {
                "ts": now.isoformat().replace("+00:00", "Z"),
                "src_ip": src,
                "dst_ip": dst,
                "src_port": rng.randint(1024, 65535),
                "dst_port": rng.choice([53, 80, 443, 8080, 22]),
                "protocol": rng.choice(protocols),
                "bytes": rng.randint(64, 1_500_000),
                "packets": rng.randint(1, 10_000),
            }
            key = f"{payload['src_ip']}-{payload['dst_ip']}"
            producer.send(args.topic, key=key, value=payload)
            n += 1
            if n % 10 == 0:
                producer.flush()
            if args.interval > 0:
                time.sleep(args.interval)
        producer.flush()
    finally:
        producer.close()


if __name__ == "__main__":
    main()
