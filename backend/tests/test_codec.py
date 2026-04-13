from __future__ import annotations

from datetime import datetime, timezone

from codec import decode_metric, encode_metric


def test_codec_roundtrip() -> None:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload = {
        "ts": now,
        "src_ip": "10.1.1.10",
        "dst_ip": "172.16.1.20",
        "src_port": 12345,
        "dst_port": 443,
        "protocol": "TCP",
        "bytes": 1024,
        "packets": 8,
    }
    encoded = encode_metric(payload)
    decoded = decode_metric(encoded)
    assert decoded == payload
