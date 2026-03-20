from pathlib import Path

from core.ai_module.temporal_memory import TemporalPatternMemory


def test_temporal_memory_store_and_find():
    db = Path('data/test_temporal.db')
    if db.exists():
        db.unlink()
    memory = TemporalPatternMemory(str(db))
    sequence = [[float(i + j) for j in range(8)] for i in range(50)]
    pattern_id = memory.store_pattern('DOGEUSDT', sequence, 0.01, 0.02, 0.03, {'symbol': 'DOGEUSDT'})
    matches = memory.find_analogues(sequence, 'DOGEUSDT', top_k=5, similarity_threshold=0.0)
    assert pattern_id in [match.pattern_id for match in matches]


def test_temporal_memory_forecast_shape():
    db = Path('data/test_temporal2.db')
    if db.exists():
        db.unlink()
    memory = TemporalPatternMemory(str(db))
    sequence = [[float(i + j) for j in range(8)] for i in range(50)]
    memory.store_pattern('DOGEUSDT', sequence, 0.01, 0.02, 0.03, {'symbol': 'DOGEUSDT'})
    forecast = memory.synthesize_forecast(memory.find_analogues(sequence, 'DOGEUSDT', top_k=5, similarity_threshold=0.0))
    assert set(forecast) == {'1h_forecast', '4h_forecast', '24h_forecast', 'confidence_interval_95', 'n_analogues'}
