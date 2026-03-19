from core.neuromorphic.snn_layer import SpikeEvent


class EventProcessor:
    def normalize(self, events: list[SpikeEvent]) -> list[dict[str, float]]:
        if not events:
            return []
        max_magnitude = max(event.magnitude for event in events) or 1.0
        return [
            {
                'neuron_id': float(event.neuron_id),
                'timestamp': event.timestamp,
                'magnitude': event.magnitude / max_magnitude,
            }
            for event in events
        ]
