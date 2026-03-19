from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from typing import Any


class EventBus:
    def __init__(self) -> None:
        self._topics: dict[str, list[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)

    async def publish(self, topic: str, event: dict[str, Any]) -> None:
        for queue in self._topics[topic]:
            await queue.put(event)

    async def subscribe(self, topic: str) -> AsyncIterator[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._topics[topic].append(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._topics[topic].remove(queue)
