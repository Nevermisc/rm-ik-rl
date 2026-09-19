#!/usr/bin/env python3
"""Test keepalive compatibility without opening a network connection."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openpi_extension.websocket_compat import call_connect_without_keepalive


def main() -> int:
    calls = []

    def legacy_connect(uri: str, *, max_size: int | None = 1024):
        calls.append(("legacy", uri, max_size))
        return "legacy-result"

    def modern_connect(
        uri: str, *, ping_interval: float | None = 20, max_size: int | None = 1024
    ):
        calls.append(("modern", uri, ping_interval, max_size))
        return "modern-result"

    assert call_connect_without_keepalive(legacy_connect, "ws://legacy", max_size=None) == "legacy-result"
    assert (
        call_connect_without_keepalive(modern_connect, "ws://modern", max_size=None)
        == "modern-result"
    )
    assert calls[0] == ("legacy", "ws://legacy", None)
    assert calls[1] == ("modern", "ws://modern", None, None)
    print(
        json.dumps(
            {
                "status": "pass",
                "legacy_api_without_ping_interval": True,
                "modern_keepalive_disabled": True,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
