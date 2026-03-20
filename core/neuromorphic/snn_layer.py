from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SpikeSample:
    timestamp: float
    amplitude: float


class SpikingNeuralLayer:
    def process(self, samples: list[SpikeSample]) -> dict[str, float | int]:
        total_energy = sum(sample.amplitude for sample in samples)
        return {'spike_count': len(samples), 'total_energy': total_energy}
