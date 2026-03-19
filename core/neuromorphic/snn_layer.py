from dataclasses import dataclass


@dataclass(slots=True)
class SpikeEvent:
    neuron_id: int
    timestamp: float
    magnitude: float


class SpikingNeuralLayer:
    def emit(self, features: list[float]) -> list[SpikeEvent]:
        return [SpikeEvent(neuron_id=index, timestamp=float(index), magnitude=value) for index, value in enumerate(features)]
