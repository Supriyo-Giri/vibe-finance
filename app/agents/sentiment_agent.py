"""
Agent 2 – Sentiment Analysis (independent of price)
"""
import time
from typing import Any, Dict
from app.agents.base import BaseAgent
from app.agents.schemas import AgentOutput, SignalLabel


class SentimentAgent(BaseAgent):
    name = "SentimentAgent"
    dimension = "news_sentiment"

    async def run(self, context: Dict[str, Any]) -> AgentOutput:
        start = time.perf_counter()
        symbol = context.get("symbol", "UNKNOWN")
        sentiment_data = context.get("sentiment_data", {})

        try:
            data = sentiment_data.get(symbol)
            if not data:
                latency = (time.perf_counter() - start) * 1000
                return self._degraded(f"No sentiment feed for {symbol}", latency)

            pos = float(data.get("positive", 0.33))
            neg = float(data.get("negative", 0.33))
            neu = float(data.get("neutral", 0.34))
            headlines = data.get("sample_headlines", [])

            signal, confidence, reason = self._classify(pos, neg, neu)

            evidence = [
                f"Positive score = {pos:.2f}",
                f"Negative score = {neg:.2f}",
                f"Neutral score  = {neu:.2f}",
                f"Net sentiment  = {pos - neg:+.2f}",
            ]
            if headlines:
                evidence.append("Headlines: " + " | ".join(headlines[:2]))

            latency = (time.perf_counter() - start) * 1000
            return self._make_output(
                signal=signal,
                confidence=round(confidence, 3),
                reasoning=reason,
                evidence=evidence,
                latency_ms=latency,
                metadata={"pos": pos, "neg": neg, "neu": neu, "net": round(pos - neg, 3)},
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return self._degraded(f"Exception in sentiment agent: {str(e)}", latency)

    def _classify(self, pos: float, neg: float, neu: float):
        net = pos - neg
        if net > 0.30 and pos > 0.45:
            return (
                SignalLabel.BULLISH,
                min(0.85, 0.55 + net),
                f"Clearly positive news flow (pos={pos:.2f}, neg={neg:.2f}, net={net:+.2f}). "
                f"Market narrative is supportive."
            )
        if net < -0.30 and neg > 0.40:
            return (
                SignalLabel.BEARISH,
                min(0.85, 0.55 + abs(net)),
                f"Clearly negative news flow (pos={pos:.2f}, neg={neg:.2f}, net={net:+.2f}). "
                f"Sentiment is a headwind."
            )
        if net > 0.12:
            return (
                SignalLabel.BULLISH,
                0.60,
                f"Mildly positive sentiment bias (net={net:+.2f}). Not extreme."
            )
        if net < -0.12:
            return (
                SignalLabel.BEARISH,
                0.59,
                f"Mildly negative sentiment bias (net={net:+.2f}). Caution warranted."
            )
        return (
            SignalLabel.NEUTRAL,
            0.50,
            f"Balanced sentiment (pos={pos:.2f}, neg={neg:.2f}, neu={neu:.2f}). "
            f"No strong narrative direction."
        )