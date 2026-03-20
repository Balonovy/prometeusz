from __future__ import annotations

from functools import lru_cache
from typing import Any

from core.ai_module.adaptive_memory import AdaptiveMemory
from core.ai_module.agent import AutonomousAgent
from core.ai_module.federation import FederatedNode
from core.ai_module.live_learner import LiveLearner
from core.ai_module.reflection_engine import ReflectionEngine
from core.ai_module.router import AIRouter
from core.ai_module.temporal_memory import TemporalPatternMemory
from core.neuromorphic.market_encoder import NeuromorphicMarketEncoder
from core.quantum_layer.consensus import QuantumConsensus
from core.quantum_layer.cloud_bridge import IBMQuantumBridge
from core.quantum_layer.correlation_graph import QuantumCorrelationGraph
from core.quantum_layer.feature_pipeline import QuantumFeaturePipeline
from core.quantum_layer.formal_verifier import FormalVerifier
from core.quantum_layer.optimizer import QuantumOptimizer
from core.quantum_layer.portfolio_engine import QuantumPortfolioEngine
from core.quantum_layer.quantum_rng import QuantumRNG
from neural_os.event_bus import EventBus
from neural_os.module_manager import ModuleManager
from neural_os.os_bridge import OSBridge
from neural_os.state_manager import StateManager
from neural_os.watchdog import SystemWatchdog
from nexus.execution_bridge import ExecutionBridge
from nexus.market_data import MarketDataClient
from nexus.risk_manager import AutonomousRiskManager
from nexus.signal_engine import SignalEngine
from nexus.veto_logic import VetoSystem


class AppContainer:
    def __init__(self) -> None:
        self.event_bus = EventBus()
        self.state_manager = StateManager()
        self.ai_router = AIRouter(self.event_bus)
        self.quantum_optimizer = QuantumOptimizer()
        self.market_data = MarketDataClient(self.event_bus)
        self.signal_engine = SignalEngine()
        self.veto_system = VetoSystem()
        self.module_manager = ModuleManager()
        self.os_bridge = OSBridge()
        self.portfolio_engine = QuantumPortfolioEngine()
        self.quantum_rng = QuantumRNG()
        self.cloud_bridge = IBMQuantumBridge()
        self.adaptive_memory = AdaptiveMemory(state_manager=self.state_manager)
        self.temporal_memory = TemporalPatternMemory()
        self.market_encoder = NeuromorphicMarketEncoder(self.event_bus)
        self.quantum_consensus = QuantumConsensus()
        self.correlation_graph = QuantumCorrelationGraph(self.event_bus)
        self.feature_pipeline = QuantumFeaturePipeline(self.temporal_memory, self.market_encoder)
        self.risk_manager = AutonomousRiskManager(self.state_manager, self.correlation_graph)
        self.reflection_engine = ReflectionEngine(self.adaptive_memory, self.ai_router, self.event_bus)
        self.live_learner = LiveLearner(self.adaptive_memory, self.state_manager, reflection_engine=self.reflection_engine)
        self.federated_node = FederatedNode(self.quantum_rng, self.live_learner, self.adaptive_memory, self.state_manager)
        self.execution_bridge = ExecutionBridge(self.quantum_rng, self.state_manager, self.event_bus, self.market_data)
        self.formal_verifier = FormalVerifier(self.veto_system, self.risk_manager, self.quantum_optimizer, self.quantum_consensus)
        self.agent = AutonomousAgent(self.event_bus, self.state_manager, self.quantum_optimizer, self.signal_engine, self.veto_system, self.market_data, adaptive_memory=self.adaptive_memory, feature_pipeline=self.feature_pipeline, temporal_memory=self.temporal_memory, quantum_consensus=self.quantum_consensus, correlation_graph=self.correlation_graph, market_encoder=self.market_encoder, portfolio_engine=self.portfolio_engine, risk_manager=self.risk_manager, live_learner=self.live_learner)
        self.watchdog = SystemWatchdog(self.event_bus, self.state_manager, {
            'quantum_optimizer': self.quantum_optimizer,
            'ai_router': self.ai_router,
            'market_data': self.market_data,
            'signal_engine': self.signal_engine,
            'event_bus': self.event_bus,
            'state_manager': self.state_manager,
            'portfolio_engine': self.portfolio_engine,
            'market_encoder': self.market_encoder,
            'agent': self.agent,
            'reflection_engine': self.reflection_engine,
            'live_learner': self.live_learner,
            'risk_manager': self.risk_manager,
            'federated_node': self.federated_node,
            'formal_verifier': self.formal_verifier,
            'cloud_bridge': self.cloud_bridge,
        })
        self._started = False

    async def startup(self) -> None:
        if self._started:
            return
        await self.market_data.start_once()
        await self.market_encoder.start()
        await self.feature_pipeline.warm_up(self.market_data)
        self.signal_engine.compute_all(self.market_data.candle_snapshot())
        await self.portfolio_engine.optimize_live(self.market_data.candle_snapshot())
        for symbol, candles in self.market_data.candle_snapshot().items():
            sequence = [[float(candle.get(key, 0.0)) for key in ('open', 'high', 'low', 'close', 'volume', 'spread', 'funding_rate')] + [float(index)] for index, candle in enumerate(candles[-50:])]
            self.temporal_memory.store_pattern(symbol, sequence, 0.01, 0.02, 0.03, {'symbol': symbol})
        self._started = True

    async def shutdown(self) -> None:
        await self.agent.stop()
        await self.watchdog.stop()
        await self.market_data.stop()
        self._started = False

    async def intelligence_overview(self) -> dict[str, Any]:
        signals = list(self.signal_engine.compute_all(self.market_data.candle_snapshot()).values())
        top_opportunities = sorted(signals, key=lambda item: item.get('confidence', 0.0), reverse=True)[:5]
        allocation = self.portfolio_engine.last_allocation or await self.portfolio_engine.optimize_live(self.market_data.candle_snapshot())
        matrix = self.watchdog.health_matrix()
        system_health = sum(1.0 for item in matrix.values() if item.get('status') == 'ok') / max(len(matrix), 1)
        return {
            'agent_decisions_last_1h': len(await self.state_manager.list_prefix('agent:decision:', limit=1000)),
            'top_opportunities': [{'pair': item['symbol'], 'action': item['action'], 'confidence': item['confidence'], 'quantum_score': item['quantum_score']} for item in top_opportunities],
            'portfolio_allocation': {'pairs': allocation.pairs, 'weights': allocation.weights, 'expected_return': allocation.expected_return, 'expected_volatility': allocation.expected_volatility, 'sharpe_ratio': allocation.sharpe_ratio, 'quantum_confidence': allocation.quantum_confidence},
            'system_health_score': system_health,
            'neuromorphic_patterns': {k: v.value for k, v in self.market_encoder.detected_patterns.items()},
            'active_vetos': self.veto_system.active_vetos(),
            'quantum_circuit_stats': self.quantum_optimizer.optimize(),
        }

    async def intelligence_master(self) -> dict[str, Any]:
        await self.startup()
        last_decision = await self.state_manager.get('agent:last_decision') or {'action': 'HOLD'}
        consensus = await self.quantum_consensus.vote([sum(vector[:8]) / 8 for vector in self.feature_pipeline.cache.values()][:8] or [0.0])
        allocation = self.portfolio_engine.last_allocation or await self.portfolio_engine.optimize_live(self.market_data.candle_snapshot())
        matrix = self.correlation_graph.build_correlation_matrix(self.market_data.candle_snapshot())
        graph_state = self.correlation_graph.encode_as_graph_state(matrix)
        cascade = self.correlation_graph.detect_cascade(graph_state, sorted(self.market_data.candle_snapshot()))
        risk = await self.risk_manager.assess(list(self.signal_engine.compute_all(self.market_data.candle_snapshot()).values()), {'pairs': allocation.pairs, 'weights': allocation.weights}, {'prices': {symbol: [row['close'] for row in candles[-20:]] for symbol, candles in self.market_data.candle_snapshot().items()}, 'cascade_alert': cascade})
        reflection = self.reflection_engine.latest() or {'accuracy_after': 0.0}
        meta = await self.reflection_engine.meta_reflect()
        reward_history = self.live_learner.reward_history()
        forecasts = {}
        analogues_found = {}
        for symbol in self.market_data.candle_snapshot().keys():
            latest = self.temporal_memory.latest_for_symbol(symbol, limit=5)
            analogues_found[symbol] = len(latest)
            forecasts[symbol] = {'1h_forecast': 0.01, '4h_forecast': 0.02, '24h_forecast': 0.03, 'confidence_interval_95': 0.01, 'n_analogues': len(latest)}
        return {
            'timestamp': __import__('time').time(),
            'agent': {'last_decision': last_decision, 'decisions_1h': len(await self.state_manager.list_prefix('agent:decision:', limit=1000)), 'cognitive_load_ms': self.agent.last_think_ms, 'learning_reward_avg': sum(item['reward'] for item in reward_history) / len(reward_history) if reward_history else 0.0},
            'quantum': {'consensus': consensus, 'portfolio': {'pairs': allocation.pairs, 'weights': allocation.weights, 'expected_return': allocation.expected_return, 'expected_volatility': allocation.expected_volatility, 'sharpe_ratio': allocation.sharpe_ratio, 'quantum_confidence': allocation.quantum_confidence}, 'correlation_cascade': cascade, 'circuit_weights': self.quantum_consensus.weights, 'last_vqe_energy': (self.quantum_optimizer.last_result or {}).get('energy')},
            'neuromorphic': {'spike_rates': self.market_encoder.health()['spike_rates'], 'detected_patterns': self.market_encoder.health()['detected_patterns'], 'active_encoders': len(self.market_encoder.spike_history)},
            'market': {'signals': self.signal_engine.compute_all(self.market_data.candle_snapshot()), 'active_vetos': self.veto_system.active_vetos(), 'regime': risk['risk_state']['regime'], 'risk_state': risk['risk_state'], 'orders': self.execution_bridge.list_orders()[-5:]},
            'intelligence': {'analogues_found': analogues_found, 'forecasts': forecasts, 'reflection_accuracy': reflection.get('accuracy_after', 0.0), 'learned_params': self.live_learner.get_params(), 'evolution_status': meta['status']},
            'infrastructure': {'watchdog_status': {name: value['status'] for name, value in self.watchdog.health_matrix().items()}, 'redis_memory_mb': 0.0, 'uptime_seconds': self.watchdog.metrics()['uptime'], 'events_per_minute': len(self.event_bus.get_recent(limit=500)) / max(self.watchdog.metrics()['uptime'] / 60, 1e-9)},
        }


@lru_cache(maxsize=1)
def get_app_container() -> AppContainer:
    return AppContainer()
