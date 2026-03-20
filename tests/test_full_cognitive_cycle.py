import asyncio
import time

from interfaces.api.dependencies import get_app_container


def test_one_full_think_cycle():
    container = get_app_container()
    asyncio.run(container.startup())
    started = time.perf_counter()
    decision = asyncio.run(container.agent.think({'prices': {symbol: [row['close'] for row in candles[-20:]] for symbol, candles in container.market_data.candle_snapshot().items()}}))
    elapsed = time.perf_counter() - started
    assert decision['action'] in ['BUY', 'SELL', 'HOLD', 'HALT']
    assert 0 <= decision['confidence'] <= 1
    assert decision['quantum_score'] is not None
    assert decision['reasoning'] != ''
    assert elapsed < 10.0
