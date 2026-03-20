from __future__ import annotations

import os
from typing import Any


class OSBridge:
    def snapshot(self) -> dict[str, Any]:
        loadavg = os.getloadavg() if hasattr(os, 'getloadavg') else (0.0, 0.0, 0.0)
        return {'pid': os.getpid(), 'loadavg': loadavg}
