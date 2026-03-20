from core.quantum_layer.correlation_graph import QuantumCorrelationGraph
from neural_os.event_bus import EventBus
from nexus.market_data import MarketDataClient


def test_correlation_graph_matrix_and_cascade():
    market = MarketDataClient(EventBus())
    graph = QuantumCorrelationGraph(EventBus())
    matrix = graph.build_correlation_matrix(market.candle_snapshot())
    state = graph.encode_as_graph_state(matrix)
    cascade = graph.detect_cascade(state, sorted(market.candle_snapshot()))
    assert len(matrix) == len(market.candle_snapshot())
    assert 'cascade_type' in cascade
