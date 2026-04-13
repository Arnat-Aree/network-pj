from __future__ import annotations

from datetime import datetime, timezone

from kafka_clickhouse_sink import _flush, parse_ts, row_from_payload


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[list[object]], list[str]]] = []

    def insert(self, table: str, rows: list[list[object]], column_names: list[str]) -> None:
        self.calls.append((table, rows, column_names))


def test_parse_ts_normalizes_utc() -> None:
    dt = parse_ts("2026-04-10T10:00:00Z")
    assert dt.tzinfo is not None
    assert dt.utcoffset() == timezone.utc.utcoffset(datetime.now(timezone.utc))


def test_row_from_payload_builds_expected_row() -> None:
    payload = {
        "ts": "2026-04-10T10:00:00Z",
        "src_ip": "10.0.0.1",
        "dst_ip": "172.16.0.1",
        "src_port": 1234,
        "dst_port": 443,
        "protocol": "TCP",
        "bytes": 1000,
        "packets": 10,
    }
    row = row_from_payload(payload)
    assert row[1:] == [
        "10.0.0.1",
        "172.16.0.1",
        1234,
        443,
        "TCP",
        1000,
        10,
    ]


def test_flush_inserts_expected_table_and_columns() -> None:
    client = FakeClient()
    rows = [[datetime.now(timezone.utc), "10.0.0.1", "172.16.0.1", 1234, 443, "TCP", 10, 1]]
    _flush(client, rows)
    assert len(client.calls) == 1
    table, inserted_rows, cols = client.calls[0]
    assert table == "network_telemetry.network_metrics"
    assert inserted_rows == rows
    assert cols == [
        "ts",
        "src_ip",
        "dst_ip",
        "src_port",
        "dst_port",
        "protocol",
        "bytes",
        "packets",
    ]
