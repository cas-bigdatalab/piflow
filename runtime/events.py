# runtime/events.py

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Awaitable, Union

log = logging.getLogger("flow.events")


Handler = Union[
    Callable[["Event"], None],
    Callable[["Event"], Awaitable[None]],
]


@dataclass
class Event:
    name: str
    payload: Dict[str, Any]
    timestamp: float
    trace_id: Optional[str] = None


class EventBus:

    def __init__(self):

        self._listeners: Dict[str, List[Handler]] = {}

    def on(self, event_name: str, handler: Handler):

        self._listeners.setdefault(event_name, []).append(handler)

    def emit(
        self,
        event_name: str,
        payload: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ):

        event = Event(
            name=event_name,
            payload=payload or {},
            timestamp=time.time(),
            trace_id=trace_id,
        )

        handlers = self._listeners.get(event_name, [])

        for handler in handlers:

            try:

                result = handler(event)

                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)

            except Exception as e:
                log.exception("event handler failed event=%s error=%s", event_name, e)


event_bus = EventBus()
