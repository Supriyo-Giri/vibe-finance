"""
Base agent class with common utilities
"""
from abc import ABC, abstractmethod
import time
from typing import Any, Dict, Optional
from app.agents.schemas import AgentOutput, AgentStatus, SignalLabel
from app.config import settings


class BaseAgent(ABC):
    name: str = "base"
    dimension: str = "generic"

    def __init__(self):
        self.last_latency_ms = 0.0

    @abstractmethod
    async def run(self, context: Dict[str, Any]) -> AgentOutput:
        """Execute the agent and return structured output."""
        pass

    def _make_output(
        self,
        signal: SignalLabel,
        confidence: float,
        reasoning: str,
        evidence: list[str] | None = None,
        citations: list | None = None,
        status: AgentStatus = AgentStatus.SUCCESS,
        metadata: dict | None = None,
        latency_ms: float = 0.0,
    ) -> AgentOutput:
        return AgentOutput(
            agent_name=self.name,
            dimension=self.dimension,
            signal=signal,
            confidence=max(0.0, min(1.0, confidence)),
            reasoning=reasoning,
            evidence=evidence or [],
            citations=citations or [],
            status=status,
            latency_ms=latency_ms,
            metadata=metadata or {},
        )

    def _degraded(self, reason: str, latency_ms: float = 0.0) -> AgentOutput:
        return self._make_output(
            signal=SignalLabel.NEUTRAL,
            confidence=0.3,
            reasoning=f"Degraded mode: {reason}. Using fallback neutral stance.",
            status=AgentStatus.DEGRADED,
            latency_ms=latency_ms,
            metadata={"degraded_reason": reason},
        )


class MockLLM:
    """Deterministic mock LLM for offline demo (no API key required)."""

    @staticmethod
    def classify_momentum(rsi: float, momentum_pct: float, volume_ratio: float) -> tuple[SignalLabel, float, str]:
        if rsi > 70 and momentum_pct > 3:
            return SignalLabel.BEARISH, 0.72, f"Overbought conditions (RSI={rsi:.1f}) with strong recent momentum ({momentum_pct:.1f}%)."
        if rsi < 30 and momentum_pct < -3:
            return SignalLabel.BULLISH, 0.75, f"Oversold (RSI={rsi:.1f}) with sharp decline ({momentum_pct:.1f}%). Mean-reversion potential."
        if momentum_pct > 2 and volume_ratio > 1.5:
            return SignalLabel.BULLISH, 0.68, f"Positive momentum ({momentum_pct:.1f}%) confirmed by elevated volume (x{volume_ratio:.1f})."
        if momentum_pct < -2 and volume_ratio > 1.5:
            return SignalLabel.BEARISH, 0.70, f"Negative momentum ({momentum_pct:.1f}%) on high volume (x{volume_ratio:.1f})."
        return SignalLabel.NEUTRAL, 0.55, f"Mixed technicals: RSI={rsi:.1f}, momentum={momentum_pct:.1f}%, volume ratio={volume_ratio:.1f}."

    @staticmethod
    def classify_sentiment(pos: float, neg: float, neu: float) -> tuple[SignalLabel, float, str]:
        score = pos - neg
        if score > 0.25:
            return SignalLabel.BULLISH, min(0.85, 0.5 + score), f"Positive sentiment dominant (pos={pos:.2f}, neg={neg:.2f})."
        if score < -0.25:
            return SignalLabel.BEARISH, min(0.85, 0.5 + abs(score)), f"Negative sentiment dominant (pos={pos:.2f}, neg={neg:.2f})."
        return SignalLabel.NEUTRAL, 0.50, f"Balanced sentiment (pos={pos:.2f}, neg={neg:.2f}, neu={neu:.2f})."

    @staticmethod
    def synthesize(agent_signals: list[dict], risk: str) -> dict:
        bull = sum(1 for a in agent_signals if a["signal"] == "bullish")
        bear = sum(1 for a in agent_signals if a["signal"] == "bearish")
        avg_conf = sum(a["confidence"] for a in agent_signals) / max(1, len(agent_signals))

        if bull > bear + 1:
            overall = "bullish"
        elif bear > bull + 1:
            overall = "bearish"
        else:
            overall = "mixed" if bull != bear else "neutral"

        # Personalization
        if risk == "conservative":
            size_lang = "Consider a small starter position (≤3% of portfolio) only if conviction is high."
            warn = "Prioritize capital preservation. Wait for clearer confirmation."
        elif risk == "aggressive":
            size_lang = "You may allocate up to your max position size if risk controls allow."
            warn = "Higher risk tolerance allows larger sizing, but respect stop-loss discipline."
        else:
            size_lang = "A moderate allocation (4-7% of portfolio) is appropriate if other factors align."
            warn = "Balance growth and downside protection."

        summary = f"Multi-agent consensus is {overall.upper()} with average confidence {avg_conf:.0%}."
        return {
            "overall_signal": overall,
            "confidence": round(avg_conf, 2),
            "summary": summary,
            "size_language": size_lang,
            "risk_warning": warn,
        }