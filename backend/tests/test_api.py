from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

import api


class DummyResult:
    def __init__(self, columns: list[str], rows: list[tuple[Any, ...]]) -> None:
        self.column_names = columns
        self.result_rows = rows


class DummyClient:
    def command(self, q: str) -> int:
        assert "SELECT 1" in q
        return 1

    def query(self, q: str, parameters: dict[str, Any]) -> DummyResult:
        if "GROUP BY src_ip" in q:
            assert parameters["lim"] == 2
            return DummyResult(
                ["src_ip", "total_bytes", "total_packets"],
                [("10.0.0.1", 2000, 20), ("10.0.0.2", 1000, 10)],
            )
        assert parameters["mins"] == 5
        return DummyResult(
            ["minute", "total_bytes", "total_packets"],
            [("2026-04-10T10:00:00", 3000, 30)],
        )


def test_health_ok() -> None:
    api.app.dependency_overrides = {}
    original = api.get_client
    api.get_client = lambda: DummyClient()
    try:
        client = TestClient(api.app)
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}
    finally:
        api.get_client = original


def test_top_talkers_ok() -> None:
    original = api.get_client
    api.get_client = lambda: DummyClient()
    try:
        client = TestClient(api.app)
        headers = {"X-API-Key": "admin-api-key"}
        r = client.get("/api/v1/top-talkers?limit=2", headers=headers)
        assert r.status_code == 200
        assert r.json()[0]["src_ip"] == "10.0.0.1"
    finally:
        api.get_client = original


def test_bandwidth_per_minute_ok() -> None:
    original = api.get_client
    api.get_client = lambda: DummyClient()
    try:
        client = TestClient(api.app)
        headers = {"X-API-Key": "admin-api-key"}
        r = client.get("/api/v1/bandwidth-per-minute?minutes=5", headers=headers)
        assert r.status_code == 200
        assert r.json()[0]["total_bytes"] == 3000
    finally:
        api.get_client = original


def test_validation_errors() -> None:
    client = TestClient(api.app)
    headers = {"X-API-Key": "admin-api-key"}
    r1 = client.get("/api/v1/top-talkers?limit=0", headers=headers)
    r2 = client.get("/api/v1/bandwidth-per-minute?minutes=0", headers=headers)
    assert r1.status_code == 400
    assert r2.status_code == 400
