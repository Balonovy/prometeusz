from __future__ import annotations

import os
from typing import Any


class OSBridge:
    def health_snapshot(self) -> dict[str, Any]:
        load = os.getloadavg() if hasattr(os, 'getloadavg') else (0.0, 0.0, 0.0)
        return {
            'cpu_load': {'1m': load[0], '5m': load[1], '15m': load[2]},
            'pid': os.getpid(),
            'cwd': os.getcwd(),
        }
