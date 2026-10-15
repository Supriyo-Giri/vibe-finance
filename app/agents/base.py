"""
Base agent class with common utilities
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
from app.agents.schemas import AgentOutput, AgentStatus, SignalLabel


class BaseAgent(ABC):
    name: str = "base"
    dimension: str = "generic"

    def __init__(self):
        self.last_latency_ms = 0.0

    @abstractmethod
    async def run(self, context: Dict[str, Any]) -> AgentOutput:
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
    def classify_momentum(rsi: float, momentum_pct: float, volume_ratio: float):
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
    def classify_sentiment(pos: float, neg: float, neu: float):
        score = pos - neg
        if score > 0.25:
            return SignalLabel.BULLISH, min(0.85, 0.5 + score), f"Positive sentiment dominant (pos={pos:.2f}, neg={neg:.2f})."
        if score < -0.25:
            return SignalLabel.BEARISH, min(0.85, 0.5 + abs(score)), f"Negative sentiment dominant (pos={pos:.2f}, neg={neg:.2f})."
        return SignalLabel.NEUTRAL, 0.50, f"Balanced sentiment (pos={pos:.2f}, neg={neg:.2f}, neu={neu:.2f})."

    @staticmethod
    def synthesize(agent_signals: list[dict], risk: str, symbol: str = "", agents_detail: list = None) -> dict:
        bull = sum(1 for a in agent_signals if a["signal"] == "bullish")
        bear = sum(1 for a in agent_signals if a["signal"] == "bearish")
        avg_conf = sum(a["confidence"] for a in agent_signals) / max(1, len(agent_signals))

        if bull > bear + 1:
            overall = "bullish"
        elif bear > bull + 1:
            overall = "bearish"
        else:
            overall = "mixed" if bull != bear else "neutral"

        agents_detail = agents_detail or []
        tech = next((a for a in agents_detail if "Momentum" in a.get("agent", "")), None)
        sent = next((a for a in agents_detail if "Sentiment" in a.get("agent", "")), None)
        fund = next((a for a in agents_detail if "Fundamental" in a.get("agent", "")), None)

        parts = []
        if tech:
            parts.append(f"Technicals are {tech['signal']} (conf {tech['confidence']:.0%})")
        if sent:
            parts.append(f"news sentiment is {sent['signal']}")
        if fund:
            parts.append(f"filings lean {fund['signal']}")
        view_str = ", ".join(parts) if parts else "mixed signals across agents"

        if overall == "bullish":
            summary = (
                f"The multi-agent view on {symbol or 'this stock'} is constructive. "
                f"{view_str.capitalize()}. Overall confidence sits at {avg_conf:.0%}."
            )
        elif overall == "bearish":
            summary = (
                f"Agents are pointing to caution on {symbol or 'this name'}. "
                f"{view_str.capitalize()}. Consensus confidence is {avg_conf:.0%}."
            )
        else:
            summary = (
                f"No clear directional consensus on {symbol or 'this stock'} yet. "
                f"{view_str.capitalize()}. Average confidence {avg_conf:.0%} — better to wait for alignment."
            )

        if risk == "conservative":
            if overall == "bullish":
                recs = [
                    "Given your capital-preservation focus, only a small starter position (max 3–4% of portfolio) makes sense even with the constructive view.",
                    "Prefer waiting for a pullback or clearer volume confirmation before adding.",
                    "Set a tight mental stop; you have historically sold winners early — plan the exit in advance.",
                ]
                warn = "Your conservative mandate means missing some upside is preferable to large drawdowns. Stay patient."
            elif overall == "bearish":
                recs = [
                    "Avoid initiating or adding to this position while the multi-agent view remains negative.",
                    "If already held, consider trimming to keep single-name risk well below your comfort threshold.",
                ]
                warn = "Capital protection comes first. There is no urgency to act on the short side either."
            else:
                recs = [
                    "With mixed signals and your conservative profile, the highest-conviction action is to do nothing for now.",
                    "Revisit only when at least two agents align and confidence exceeds ~65%.",
                ]
                warn = "Sitting in cash or existing holdings is a valid decision when clarity is low."
        elif risk == "aggressive":
            if overall == "bullish":
                recs = [
                    "Your higher risk tolerance allows a meaningful allocation (up to your stated max position size) provided you define risk levels first.",
                    "Consider scaling in over 2–3 tranches rather than all at once, especially if volume is still building.",
                    "Keep a clear invalidation level — aggressive sizing still needs disciplined exits.",
                ]
                warn = "Larger size is acceptable for you, but position sizing without a stop is still gambling."
            elif overall == "bearish":
                recs = [
                    "Even with aggressive tolerance, fighting a multi-agent bearish consensus is low-odds. Reduce or avoid new longs.",
                    "If you want to express a short-term view, keep size modest and time-stop the idea within a few sessions.",
                ]
                warn = "High risk tolerance is not a licence to ignore deteriorating technicals and sentiment."
            else:
                recs = [
                    "Mixed signals give you room for a small tactical probe (2–4%), but treat it as a test, not a core holding.",
                    "Define both upside target and hard stop before entry; abandon quickly if agents stay split.",
                ]
                warn = "Your edge comes from size + speed of decision, not from forcing conviction where none exists."
        else:  # moderate
            if overall == "bullish":
                recs = [
                    "A measured 5–8% allocation is consistent with your moderate profile if the technical and fundamental agents stay supportive.",
                    "Scale in gradually and keep an eye on any shift in news sentiment.",
                    "Review the position after the next major data point (earnings or macro print).",
                ]
                warn = "Balance remains the key word — neither maximum aggression nor excessive caution."
            elif overall == "bearish":
                recs = [
                    "Stay on the sidelines for new capital. Existing exposure can be reduced toward your lower comfort band.",
                    "Use any short-term bounce as an opportunity to lighten rather than add.",
                ]
                warn = "Moderate investors do best by avoiding the need to be heroic on either side."
            else:
                recs = [
                    "No strong edge right now. Maintain current holdings and wait for clearer multi-agent alignment.",
                    "A small watchlist alert on volume or RSI extremes is more useful than forcing a trade.",
                ]
                warn = "Patience is a position. Mixed readings rarely reward urgency."

        return {
            "overall_signal": overall,
            "confidence": round(avg_conf, 2),
            "summary": summary,
            "recommendations": recs,
            "risk_warning": warn,
        }