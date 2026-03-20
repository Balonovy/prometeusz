import asyncio
import tracemalloc

from fastapi.testclient import TestClient

from interfaces.api.main import app
from neural_os.event_bus import EventBus
from nexus.market_data import MarketDataClient
from nexus.signal_engine import SignalEngine
from nexus.veto_logic import VetoSystem


def test_signal_engine_and_veto_logic() -> None:
    bus = EventBus()
    market = MarketDataClient(bus)
    signal = SignalEngine().generate_signal('DOGEUSDT', market.latest_candles('DOGEUSDT'))
    decision = VetoSystem().evaluate(signal, market.latest_candles('DOGEUSDT', 1)[-1])
    assert decision['status'] in {'CLEAR', 'VETO'}


def test_nexus_health_endpoint() -> None:
    with TestClient(app) as client:
        assert client.get('/nexus/health').status_code == 200


def test_nexus_market_endpoint() -> None:
    with TestClient(app) as client:
        assert client.get('/nexus/market/latest').status_code == 200


def test_nexus_signals_endpoint() -> None:
    with TestClient(app) as client:
        assert client.get('/nexus/signals').status_code == 200


def test_signal_generation_sol() -> None:
    signal = SignalEngine().generate_signal('SOLUSDT', MarketDataClient(EventBus()).latest_candles('SOLUSDT'))
    assert signal['symbol'] == 'SOLUSDT'


def test_signal_generation_avax() -> None:
    signal = SignalEngine().generate_signal('AVAXUSDT', MarketDataClient(EventBus()).latest_candles('AVAXUSDT'))
    assert signal['symbol'] == 'AVAXUSDT'


def test_signal_generation_doge() -> None:
    signal = SignalEngine().generate_signal('DOGEUSDT', MarketDataClient(EventBus()).latest_candles('DOGEUSDT'))
    assert signal['symbol'] == 'DOGEUSDT'


def test_signal_generation_matic() -> None:
    signal = SignalEngine().generate_signal('MATICUSDT', MarketDataClient(EventBus()).latest_candles('MATICUSDT'))
    assert signal['symbol'] == 'MATICUSDT'


def test_signal_generation_link() -> None:
    signal = SignalEngine().generate_signal('LINKUSDT', MarketDataClient(EventBus()).latest_candles('LINKUSDT'))
    assert signal['symbol'] == 'LINKUSDT'


def test_signal_generation_dot() -> None:
    signal = SignalEngine().generate_signal('DOTUSDT', MarketDataClient(EventBus()).latest_candles('DOTUSDT'))
    assert signal['symbol'] == 'DOTUSDT'


def test_signal_generation_ada() -> None:
    signal = SignalEngine().generate_signal('ADAUSDT', MarketDataClient(EventBus()).latest_candles('ADAUSDT'))
    assert signal['symbol'] == 'ADAUSDT'


def test_signal_generation_xrp() -> None:
    signal = SignalEngine().generate_signal('XRPUSDT', MarketDataClient(EventBus()).latest_candles('XRPUSDT'))
    assert signal['symbol'] == 'XRPUSDT'


def test_signal_generation_ltc() -> None:
    signal = SignalEngine().generate_signal('LTCUSDT', MarketDataClient(EventBus()).latest_candles('LTCUSDT'))
    assert signal['symbol'] == 'LTCUSDT'


def test_signal_generation_atom() -> None:
    signal = SignalEngine().generate_signal('ATOMUSDT', MarketDataClient(EventBus()).latest_candles('ATOMUSDT'))
    assert signal['symbol'] == 'ATOMUSDT'


def test_market_data_publishes_mock_events() -> None:
    bus = EventBus()
    market = MarketDataClient(bus)
    asyncio.run(market.start_once())
    recent = bus.get_recent('nexus.candle.', limit=25)
    assert recent


def test_memory_stability_after_100_iterations() -> None:
    bus = EventBus()
    market = MarketDataClient(bus)
    engine = SignalEngine()
    tracemalloc.start()
    for _ in range(100):
        asyncio.run(market.start_once())
        engine.compute_all(market.candle_snapshot())
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert peak - current < 2_000_000


def test_veto_near() -> None:
    market = MarketDataClient(EventBus())
    signal = SignalEngine().generate_signal('NEARUSDT', market.latest_candles('NEARUSDT'))
    veto = VetoSystem().evaluate(signal, market.latest_candles('NEARUSDT', 1)[-1])
    assert set(veto.keys()) >= {'status', 'pair', 'reasons'}


def test_veto_apt() -> None:
    market = MarketDataClient(EventBus())
    signal = SignalEngine().generate_signal('APTUSDT', market.latest_candles('APTUSDT'))
    veto = VetoSystem().evaluate(signal, market.latest_candles('APTUSDT', 1)[-1])
    assert set(veto.keys()) >= {'status', 'pair', 'reasons'}


def test_veto_arb() -> None:
    market = MarketDataClient(EventBus())
    signal = SignalEngine().generate_signal('ARBUSDT', market.latest_candles('ARBUSDT'))
    veto = VetoSystem().evaluate(signal, market.latest_candles('ARBUSDT', 1)[-1])
    assert set(veto.keys()) >= {'status', 'pair', 'reasons'}


def test_veto_op() -> None:
    market = MarketDataClient(EventBus())
    signal = SignalEngine().generate_signal('OPUSDT', market.latest_candles('OPUSDT'))
    veto = VetoSystem().evaluate(signal, market.latest_candles('OPUSDT', 1)[-1])
    assert set(veto.keys()) >= {'status', 'pair', 'reasons'}


def test_veto_inj() -> None:
    market = MarketDataClient(EventBus())
    signal = SignalEngine().generate_signal('INJUSDT', market.latest_candles('INJUSDT'))
    veto = VetoSystem().evaluate(signal, market.latest_candles('INJUSDT', 1)[-1])
    assert set(veto.keys()) >= {'status', 'pair', 'reasons'}


def test_veto_sui() -> None:
    market = MarketDataClient(EventBus())
    signal = SignalEngine().generate_signal('SUIUSDT', market.latest_candles('SUIUSDT'))
    veto = VetoSystem().evaluate(signal, market.latest_candles('SUIUSDT', 1)[-1])
    assert set(veto.keys()) >= {'status', 'pair', 'reasons'}


def test_veto_sei() -> None:
    market = MarketDataClient(EventBus())
    signal = SignalEngine().generate_signal('SEIUSDT', market.latest_candles('SEIUSDT'))
    veto = VetoSystem().evaluate(signal, market.latest_candles('SEIUSDT', 1)[-1])
    assert set(veto.keys()) >= {'status', 'pair', 'reasons'}


def test_veto_tia() -> None:
    market = MarketDataClient(EventBus())
    signal = SignalEngine().generate_signal('TIAUSDT', market.latest_candles('TIAUSDT'))
    veto = VetoSystem().evaluate(signal, market.latest_candles('TIAUSDT', 1)[-1])
    assert set(veto.keys()) >= {'status', 'pair', 'reasons'}


def test_veto_jasmy() -> None:
    market = MarketDataClient(EventBus())
    signal = SignalEngine().generate_signal('JASMYUSDT', market.latest_candles('JASMYUSDT'))
    veto = VetoSystem().evaluate(signal, market.latest_candles('JASMYUSDT', 1)[-1])
    assert set(veto.keys()) >= {'status', 'pair', 'reasons'}


def test_veto_wif() -> None:
    market = MarketDataClient(EventBus())
    signal = SignalEngine().generate_signal('WIFUSDT', market.latest_candles('WIFUSDT'))
    veto = VetoSystem().evaluate(signal, market.latest_candles('WIFUSDT', 1)[-1])
    assert set(veto.keys()) >= {'status', 'pair', 'reasons'}
