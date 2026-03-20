from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any

from core.ai_module.adaptive_memory import AdaptiveMemory
from core.ai_module.engine import ChatMessage, LLMEngine


class AutonomousAgent:
    def __init__(self, event_bus: Any, state_manager: Any, quantum_optimizer: Any, signal_engine: Any, veto_system: Any, market_data: Any, adaptive_memory: AdaptiveMemory | None = None, llm_engine: LLMEngine | None = None, interval_seconds: float = 5.0, feature_pipeline: Any | None = None, temporal_memory: Any | None = None, quantum_consensus: Any | None = None, correlation_graph: Any | None = None, market_encoder: Any | None = None, portfolio_engine: Any | None = None, risk_manager: Any | None = None, live_learner: Any | None = None) -> None:
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.quantum_optimizer = quantum_optimizer
        self.signal_engine = signal_engine
        self.veto_system = veto_system
        self.market_data = market_data
        self.adaptive_memory = adaptive_memory or AdaptiveMemory(state_manager=state_manager)
        self.llm_engine = llm_engine or LLMEngine()
        self.interval_seconds = interval_seconds
        self.feature_pipeline = feature_pipeline
        self.temporal_memory = temporal_memory
        self.quantum_consensus = quantum_consensus
        self.correlation_graph = correlation_graph
        self.market_encoder = market_encoder
        self.portfolio_engine = portfolio_engine
        self.risk_manager = risk_manager
        self.live_learner = live_learner
        self._running = False
        self._halted = False
        self._task: asyncio.Task[None] | None = None
        self.decisions_made = 0
        self.last_think_ms = 0.0
        self._recent_decisions: list[dict[str, Any]] = []

    async def start(self) -> None:
        if self._task is None:
            self._running = True
            self._task = asyncio.create_task(self.run(), name='autonomous-agent')

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def run(self) -> None:
        self._running = True
        while self._running and not self._halted:
            decision = await self.think({'events': self.event_bus.poll_events('nexus.*', limit=200), 'prices': {symbol: [row['close'] for row in candles[-20:]] for symbol, candles in self.market_data.candle_snapshot().items()}})
            await self.reflect()
            await self.state_manager.set('agent:status', {'status': 'ok', 'decisions_made': self.decisions_made, 'last_decision': decision}, ttl=3600)
            await asyncio.sleep(self.interval_seconds)

    async def think(self, market_state: dict[str, Any]) -> dict[str, Any]:
        started = time.perf_counter()
        candles = self.market_data.candle_snapshot()
        symbols = list(candles)
        feature_map = {}
        analogue_map: dict[str, list[Any]] = {}
        for symbol in symbols:
            if self.feature_pipeline and symbol in self.feature_pipeline.cache:
                feature_map[symbol] = self.feature_pipeline.cache[symbol]
            else:
                feature_map[symbol] = self.feature_pipeline.transform(symbol, candles[symbol]) if self.feature_pipeline else [0.0] * 64
        consensus = await self.quantum_consensus.vote([sum(values[:8]) / 8 for values in feature_map.values()][:8]) if self.quantum_consensus else {'consensus_direction': 0, 'consensus_confidence': 0.5, 'agreement_ratio': 0.0, 'dissenting_circuits': [], 'fault_tolerance': False}
        corr_matrix = self.correlation_graph.build_correlation_matrix(candles) if self.correlation_graph else []
        graph_state = self.correlation_graph.encode_as_graph_state(corr_matrix) if self.correlation_graph else []
        cascade = self.correlation_graph.detect_cascade(graph_state, sorted(candles)) if self.correlation_graph else {'triggered': False, 'affected_pairs': [], 'cascade_type': 'rotation', 'quantum_coherence': 0.0, 'recommended_action': 'OBSERVE'}
        patterns = {symbol: pattern.value for symbol, pattern in getattr(self.market_encoder, 'detected_patterns', {}).items()} if self.market_encoder else {}
        signals = self.signal_engine.compute_all(candles)
        top_symbols = sorted(signals, key=lambda symbol: signals[symbol]['confidence'], reverse=True)[:3]
        for symbol in top_symbols:
            if self.temporal_memory is not None:
                sequence = [[float(candle.get(key, 0.0)) for key in ('open', 'high', 'low', 'close', 'volume', 'spread', 'funding_rate')] + [float(index)] for index, candle in enumerate(candles[symbol][-50:])]
                analogue_map[symbol] = self.temporal_memory.find_analogues(sequence, symbol, top_k=5, similarity_threshold=0.0)
        vetoes = {symbol: self.veto_system.evaluate(signal, self.market_data.latest_candles(symbol, 1)[-1]) for symbol, signal in signals.items()}
        for symbol, veto in vetoes.items():
            await self.event_bus.publish(f'nexus.veto.{symbol}', veto)
        portfolio = await self.portfolio_engine.optimize_live(candles) if self.portfolio_engine else None
        portfolio_payload = {'pairs': portfolio.pairs, 'weights': portfolio.weights, 'expected_return': portfolio.expected_return, 'expected_volatility': portfolio.expected_volatility, 'sharpe_ratio': portfolio.sharpe_ratio, 'quantum_confidence': portfolio.quantum_confidence} if portfolio else {'pairs': [], 'weights': []}
        risk = await self.risk_manager.assess(list(signals.values()), portfolio_payload, {'prices': market_state.get('prices', {}), 'cascade_alert': cascade, 'drawdown_current': market_state.get('drawdown_current', 0.0), 'var_95_1h': market_state.get('var_95_1h', 0.0)}) if self.risk_manager else {'hard_blocked': False, 'risk_state': {'regime': 'ranging'}, 'position_scale': 1.0}
        if risk['hard_blocked']:
            decision = {'decision_id': str(uuid.uuid4()), 'pair': 'PORTFOLIO', 'action': 'HALT', 'confidence': 1.0, 'reasoning': 'Risk manager hard block triggered.', 'risk_level': 'critical', 'quantum_score': cascade.get('quantum_coherence', 0.0), 'timestamp': time.time()}
        else:
            best_symbol = max(signals, key=lambda symbol: signals[symbol]['confidence'])
            synthesis_payload = {'signals': signals, 'quantum_consensus': consensus, 'cascade_alert': cascade, 'neuromorphic_patterns': patterns, 'historical_analogues': {key: [{'pattern_id': match.pattern_id, 'similarity': match.similarity, 'outcome_distribution': match.outcome_distribution, 'context_overlap': match.context_overlap, 'timestamp_original': match.timestamp_original} for match in value] for key, value in analogue_map.items()}, 'portfolio': portfolio_payload, 'risk_state': risk, 'learned_params': self.live_learner.get_params() if self.live_learner else {}, 'focus_symbol': best_symbol}
            await self.event_bus.publish('consciousness.perception', {'symbol': best_symbol, 'features_shape': len(feature_map[best_symbol]), 'spike_count': len(getattr(self.market_encoder, 'spike_history', {}).get(best_symbol, [])) if self.market_encoder else 0, 'analogue_found': len(analogue_map.get(best_symbol, []))})
            result = await self.llm_engine.chat([ChatMessage(role='system', content=self.adaptive_memory.get_current_system_prompt()), ChatMessage(role='user', content=json.dumps(synthesis_payload))], response_format='json')
            content = json.loads(result['message']['content'])
            signal = signals[best_symbol]
            decision = {'decision_id': str(uuid.uuid4()), 'pair': content.get('pair', best_symbol), 'action': content.get('action', signal['action']), 'confidence': float(content.get('confidence', signal['confidence'])), 'reasoning': content.get('reasoning', 'Aggregated cognitive cycle output.'), 'risk_level': content.get('risk_level', 'medium'), 'quantum_score': consensus['consensus_confidence'], 'timestamp': time.time(), 'consensus': consensus, 'cascade': cascade, 'risk_state': risk['risk_state']}
            await self.event_bus.publish('consciousness.reasoning', {'step': 'llm_synthesis', 'input_tokens': len(json.dumps(synthesis_payload).split()), 'output_preview': decision['reasoning'][:80], 'duration_ms': 0.0})
        self.decisions_made += 1
        self._recent_decisions.append(decision)
        self._recent_decisions = self._recent_decisions[-100:]
        self.last_think_ms = (time.perf_counter() - started) * 1000
        await self.adaptive_memory.record_decision(decision)
        await self.state_manager.set('agent:last_decision', decision, ttl=3600)
        await self.state_manager.set(f"agent:decision:{decision['decision_id']}", decision, ttl=3600)
        await self.event_bus.publish('agent.decision', decision)
        if self.live_learner is not None:
            await self.event_bus.publish('consciousness.learning', {'param_count': len(self.live_learner.get_params()), 'decision_id': decision['decision_id']})
        return decision

    async def reflect(self) -> float:
        recent = self._recent_decisions[-10:]
        if not recent:
            return 1.0
        score = sum(item['confidence'] for item in recent) / len(recent)
        await self.state_manager.set('agent:accuracy_drift', {'accuracy_score': score, 'sample_size': len(recent)}, ttl=3600)
        return float(score)

    async def emergency_halt(self) -> None:
        self._halted = True
        await self.event_bus.publish('agent.halt', {'timestamp': time.time(), 'reason': 'manual'})

    def health(self) -> dict[str, Any]:
        return {'status': 'ok' if not self._halted else 'halted', 'loop_status': 'running' if self._running and not self._halted else 'stopped', 'decisions_made': self.decisions_made, 'last_think_ms': self.last_think_ms, 'response_time_ms': self.last_think_ms}


async def main() -> None:
    from interfaces.api.dependencies import get_app_container

    container = get_app_container()
    await container.startup()
    await container.agent.run()


if __name__ == '__main__':
    asyncio.run(main())
