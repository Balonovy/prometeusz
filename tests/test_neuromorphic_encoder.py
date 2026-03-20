import asyncio

from core.neuromorphic.market_encoder import NeuromorphicMarketEncoder, PatternType
from neural_os.event_bus import EventBus


async def _feed(prices):
    for price in prices:
        yield price


def test_encode_stream_yields_spikes():
    encoder = NeuromorphicMarketEncoder(EventBus(), refractory_period=0.0)

    async def collect():
        spikes = []
        async for spike in encoder.encode_stream('DOGEUSDT', _feed([1.0, 1.003, 1.006, 1.009])):
            spikes.append(spike)
        return spikes

    spikes = asyncio.run(collect())
    assert spikes


def test_pattern_detection_returns_enum_accumulation():
    encoder = NeuromorphicMarketEncoder(EventBus(), refractory_period=0.0)
    ts = 0.0
    for price in [1.0, 1.002, 1.004, 1.006, 1.008, 1.01]:
        ts += 1.0
        encoder._encode_price('DOGEUSDT', price, ts)
    detected = encoder.detect_pattern(list(encoder.spike_history['DOGEUSDT']))
    assert isinstance(detected, PatternType)


def test_pattern_detection_returns_enum_distribution():
    encoder = NeuromorphicMarketEncoder(EventBus(), refractory_period=0.0)
    ts = 0.0
    for price in [1.01, 1.008, 1.006, 1.004, 1.002, 1.0]:
        ts += 1.0
        encoder._encode_price('DOGEUSDT', price, ts)
    detected = encoder.detect_pattern(list(encoder.spike_history['DOGEUSDT']))
    assert isinstance(detected, PatternType)


def test_encoder_publishes_pattern_events():
    bus = EventBus()
    encoder = NeuromorphicMarketEncoder(bus, refractory_period=0.0)

    async def runner():
        await encoder.start()
        for price in [1.0, 1.003, 1.006, 1.009]:
            await encoder.on_candle({'symbol': 'DOGEUSDT', 'close': price})

    asyncio.run(runner())
    assert bus.poll_events('neuromorphic.pattern.*')


def test_encoder_health_shape():
    encoder = NeuromorphicMarketEncoder(EventBus())
    health = encoder.health()
    assert health['status'] == 'ok'
