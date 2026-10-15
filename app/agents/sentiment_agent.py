"""
Agent 2 – Sentiment Analysis
Dimension: Market Sentiment
"""
import time
from typing import Any, Dict
from app.agents.base import BaseAgent, MockLLM
from app.agents.schemas import AgentOutput, SignalLabel


class SentimentAgent(BaseAgent):
    name = "SentimentAgent"
    dimension = "sentiment"

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

            signal, confidence, reason = MockLLM.classify_sentiment(pos, neg, neu)

            evidence = [
                f"Positive score: {pos:.2f}",
                f"Negative score: {neg:.2f}",
                f"Neutral score: {neu:.2f}",
            ]
            if headlines:
                evidence.append(f"Sample headlines: {'; '.join(headlines[:2])}")

            latency = (time.perf_counter() - start) * 1000
            return self._make_output(
                signal=signal,
                confidence=confidence,
                reasoning=reason,
                evidence=evidence,
                latency_ms=latency,
                metadata={"pos": pos, "neg": neg, "neu": neu},
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return self._degraded(f"Exception in sentiment agent: {str(e)}", latency)