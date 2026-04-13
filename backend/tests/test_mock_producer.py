from __future__ import annotations

import random
import socket

from mock_producer import random_ipv4


def test_random_ipv4_returns_valid_ipv4() -> None:
    ip = random_ipv4(random.Random(42))
    parsed = socket.inet_aton(ip)
    assert isinstance(parsed, bytes)
    assert len(parsed) == 4
