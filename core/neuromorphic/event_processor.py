from __future__ import annotations

from typing import Any


class EventProcessor:
    def normalize(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {'event_type': payload.get('event_type', 'unknown'), 'payload': payload}
