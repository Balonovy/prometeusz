from __future__ import annotations

import asyncio
import fnmatch
from collections import defaultdict, deque
from dataclasses import dataclass
from time import time
from typing import Any, Awaitable, Callable

Subscriber = Callable[[dict[str, Any]], Awaitable[None] | None]


@dataclass(slots=True)
class EventRecord:
    topic: str
    payload: dict[str, Any]
    timestamp: float


class EventBus:
    def __init__(self, history_limit: int = 2000) -> None:
        self._subscribers: dict[str, list[Subscriber]] = defaultdict(list)
        self._pattern_subscribers: list[tuple[str, Subscriber]] = []
        self._published: dict[str, int] = defaultdict(int)
        self._history: deque[EventRecord] = deque(maxlen=history_limit)
        self._lock = asyncio.Lock()

    def subscribe(self, topic: str, subscriber: Subscriber) -> None:
        self._subscribers[topic].append(subscriber)

    def subscribe_pattern(self, pattern: str, subscriber: Subscriber) -> None:
        self._pattern_subscribers.append((pattern, subscriber))

    def _matches(self, pattern: str, topic: str) -> bool:
        translated = pattern.replace('#', '*')
        return fnmatch.fnmatch(topic, translated)

    async def publish(self, topic: str, payload: dict[str, Any]) -> None:
        record = EventRecord(topic=topic, payload=payload, timestamp=time())
        async with self._lock:
            self._published[topic] += 1
            self._history.append(record)
        subscribers = list(self._subscribers.get(topic, []))
        for pattern, subscriber in self._pattern_subscribers:
            if self._matches(pattern, topic):
                subscribers.append(subscriber)
        if subscribers:
            await asyncio.gather(*(self._dispatch(subscriber, payload) for subscriber in subscribers))

    async def _dispatch(self, subscriber: Subscriber, payload: dict[str, Any]) -> None:
        result = subscriber(payload)
        if asyncio.iscoroutine(result):
            await result

    def get_recent(self, topic_prefix: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        items = list(self._history)
        if topic_prefix:
            items = [item for item in items if item.topic.startswith(topic_prefix)]
        return [{'topic': item.topic, 'payload': item.payload, 'timestamp': item.timestamp} for item in items[-limit:]]

    def poll_events(self, pattern: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        items = list(self._history)
        if pattern:
            items = [item for item in items if self._matches(pattern, item.topic)]
        return [{'topic': item.topic, 'payload': item.payload, 'timestamp': item.timestamp} for item in items[-limit:]]

    def stats(self) -> dict[str, Any]:
        return {
            'status': 'ok',
            'topics': {topic: len(subscribers) for topic, subscribers in self._subscribers.items()},
            'pattern_topics': [pattern for pattern, _ in self._pattern_subscribers],
            'published': dict(self._published),
            'history_size': len(self._history),
        }

    def health(self) -> dict[str, Any]:
        return {'status': 'ok', 'response_time_ms': 0.0, 'history_size': len(self._history)}
