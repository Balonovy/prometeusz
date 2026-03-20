from core.ai_module.temporal_memory import TemporalPatternMemory
from core.quantum_layer.feature_pipeline import QuantumFeaturePipeline
from neural_os.event_bus import EventBus
from nexus.market_data import MarketDataClient


def test_feature_pipeline_transform_shape():
    market = MarketDataClient(EventBus())
    temporal = TemporalPatternMemory('data/test_feature_temporal.db')
    pipeline = QuantumFeaturePipeline(temporal)
    vector = pipeline.transform('DOGEUSDT', market.latest_candles('DOGEUSDT', 50))
    assert len(vector) == 64


def test_feature_pipeline_labels():
    market = MarketDataClient(EventBus())
    temporal = TemporalPatternMemory('data/test_feature_temporal2.db')
    pipeline = QuantumFeaturePipeline(temporal)
    pipeline.transform('DOGEUSDT', market.latest_candles('DOGEUSDT', 50))
    labeled = pipeline.labeled_features('DOGEUSDT')
    assert labeled['shape'] == 64
