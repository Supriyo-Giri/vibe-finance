# app/agents/momentum_agent.py
"""
Agent 1 – Price Momentum & Volume Anomaly
Dimension: Technical (Price + Volume)
"""
import time
from typing import Any, Dict
from app.agents.base import BaseAgent, MockLLM
from app.agents.schemas import AgentOutput, SignalLabel


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

            # Multi-factor classification with explicit confidence rules
            signal, confidence, reason = self._classify(rsi, momentum_pct, volume_ratio, change_1d)

            evidence = [
                f"RSI(14) = {rsi:.1f}  → {'Overbought' if rsi > 70 else 'Oversold' if rsi < 30 else 'Neutral zone'}",
                f"5-day momentum = {momentum_pct:+.2f}%",
                f"1-day change = {change_1d:+.2f}%",
                f"Volume ratio (vs 20d avg) = {volume_ratio:.2f}x",
                f"Last price = ₹{current:.2f}",
            ]

            if volume_ratio > 2.0:
                evidence.append("⚠ Volume anomaly detected (>2× average) – increases conviction")
                confidence = min(0.92, confidence + 0.08)
            elif volume_ratio < 0.6:
                evidence.append("Low volume – signal reliability reduced")
                confidence = max(0.35, confidence - 0.10)

            latency = (time.perf_counter() - start) * 1000
            return self._make_output(
                signal=signal,
                confidence=round(confidence, 3),
                reasoning=reason,
                evidence=evidence,
                latency_ms=latency,
                metadata={
                    "rsi": rsi,
                    "momentum_5d": momentum_pct,
                    "volume_ratio": volume_ratio,
                    "change_1d": change_1d,
                },
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return self._degraded(f"Exception in momentum agent: {str(e)}", latency)

    def _classify(self, rsi: float, mom: float, vol: float, change_1d: float):
        """Explicit multi-factor rules with calibrated confidence."""
        # Strong bullish
        if mom > 3.5 and vol > 1.4 and rsi < 68:
            return (
                SignalLabel.BULLISH,
                0.78,
                f"Strong positive momentum ({mom:+.1f}%) confirmed by elevated volume ({vol:.1f}×) "
                f"while RSI remains below overbought territory ({rsi:.1f})."
            )
        # Strong bearish
        if mom < -3.5 and vol > 1.4 and rsi > 32:
            return (
                SignalLabel.BEARISH,
                0.76,
                f"Strong negative momentum ({mom:+.1f}%) on high volume ({vol:.1f}×). "
                f"RSI={rsi:.1f} still leaves room for further downside."
            )
        # Overbought mean-reversion
        if rsi > 72 and mom > 2:
            return (
                SignalLabel.BEARISH,
                0.71,
                f"Overbought conditions (RSI={rsi:.1f}) after strong run ({mom:+.1f}%). "
                f"Elevated risk of short-term pullback."
            )
        # Oversold mean-reversion
        if rsi < 28 and mom < -2:
            return (
                SignalLabel.BULLISH,
                0.73,
                f"Oversold (RSI={rsi:.1f}) after sharp decline ({mom:+.1f}%). "
                f"Mean-reversion setup with potential bounce."
            )
        # Mild bullish
        if mom > 1.5 and change_1d > 0:
            return (
                SignalLabel.BULLISH,
                0.62,
                f"Positive short-term momentum ({mom:+.1f}%, today {change_1d:+.1f}%). "
                f"RSI={rsi:.1f} is constructive but not extreme."
            )
        # Mild bearish
        if mom < -1.5 and change_1d < 0:
            return (
                SignalLabel.BEARISH,
                0.61,
                f"Negative short-term momentum ({mom:+.1f}%, today {change_1d:+.1f}%). "
                f"RSI={rsi:.1f}."
            )
        # Neutral / mixed
        return (
            SignalLabel.NEUTRAL,
            0.52,
            f"Mixed technical picture: RSI={rsi:.1f}, 5d momentum={mom:+.1f}%, "
            f"volume={vol:.1f}×. No dominant directional bias."
        )