"""Compatibility helpers for websockets versions bundled by OpenPI and Isaac Sim."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any


def call_connect_without_keepalive(
    connect: Callable[..., Any], *args: Any, **kwargs: Any
) -> Any:
    """Disable sync-client keepalive only when the installed API supports it.

    websockets 12 (bundled with Isaac Sim 5.1) has no sync-client
    ``ping_interval`` parameter. websockets 15 (used by OpenPI) does. The
    version check is based on the callable signature so vendored builds work.
    """

    parameters = inspect.signature(connect).parameters
    if "ping_interval" in parameters:
        kwargs["ping_interval"] = None
    else:
        kwargs.pop("ping_interval", None)
    return connect(*args, **kwargs)
