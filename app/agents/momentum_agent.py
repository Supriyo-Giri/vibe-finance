"""
Agent 1 – Price Momentum & Volume Anomaly
Dimension: Technical / Momentum
"""
import time
from typing import Any, Dict
from app.agents.base import BaseAgent, MockLLM
from app.agents.schemas import AgentOutput, SignalLabel, AgentStatus


class MomentumAgent(BaseAgent):
    name = "MomentumAgent"
    dimension = "price_momentum_volume"

    async def run(self, context: Dict[str, Any]) -> AgentOutput:
        start = time.perf_counter()
        symbol = context.get("symbol", "UNKNOWN")
        market = context.get("market_data", {})

        try:
            price_data = market.get(symbol)
            if not price_data:
                latency = (time.perf_counter() - start) * 1000
                return self._degraded(f"No price data available for {symbol}", latency)

            rsi = float(price_data.get("rsi_14", 50))
            momentum_pct = float(price_data.get("momentum_5d_pct", 0))
            volume_ratio = float(price_data.get("volume_ratio", 1.0))
            current = float(price_data.get("last_price", 0))
            change_1d = float(price_data.get("change_1d_pct", 0))

            signal, confidence, reason = MockLLM.classify_momentum(rsi, momentum_pct, volume_ratio)

            evidence = [
                f"RSI(14) = {rsi:.1f}",
                f"5-day momentum = {momentum_pct:+.2f}%",
                f"Volume vs 20-day avg = {volume_ratio:.2f}x",
                f"Last price = ₹{current:.2f} ({change_1d:+.2f}% today)",
            ]

            # Extra volume anomaly flag
            if volume_ratio > 2.0:
                evidence.append(f"Volume anomaly detected (>2x average)")
                confidence = min(0.9, confidence + 0.08)

            latency = (time.perf_counter() - start) * 1000
            return self._make_output(
                signal=signal,
                confidence=confidence,
                reasoning=reason,
                evidence=evidence,
                latency_ms=latency,
                metadata={
                    "rsi": rsi,
                    "momentum_5d": momentum_pct,
                    "volume_ratio": volume_ratio,
                },
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return self._degraded(f"Exception in momentum agent: {str(e)}", latency)