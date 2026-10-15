"""
Agent 3 – Fundamental / RAG Agent
Dimension: Regulatory filings & earnings (Retrieval-Augmented)
"""
import time
from typing import Any, Dict
from app.agents.base import BaseAgent
from app.agents.schemas import AgentOutput, SignalLabel, Citation, AgentStatus
from app.rag.retriever import DocumentRetriever


class FundamentalAgent(BaseAgent):
    name = "FundamentalAgent"
    dimension = "fundamental_rag"

    def __init__(self, retriever: DocumentRetriever | None = None):
        super().__init__()
        self.retriever = retriever or DocumentRetriever()

    async def run(self, context: Dict[str, Any]) -> AgentOutput:
        start = time.perf_counter()
        symbol = context.get("symbol", "UNKNOWN")
        company_name = context.get("company_name", symbol)

        try:
            # Force degradation if requested (for demo of graceful failure)
            if context.get("force_rag_failure"):
                latency = (time.perf_counter() - start) * 1000
                return self._degraded("Simulated missing financial filings", latency)

            query = f"{company_name} {symbol} earnings financial results outlook risks growth"
            docs = self.retriever.retrieve(query, symbol=symbol, top_k=3)

            if not docs:
                latency = (time.perf_counter() - start) * 1000
                return self._degraded(f"No relevant filings found for {symbol}", latency)

            citations = []
            evidence = []
            bullish_keywords = ["growth", "profit", "increase", "strong", "beat", "record", "expansion"]
            bearish_keywords = ["decline", "loss", "risk", "challenge", "pressure", "slowdown", "margin"]

            bull_score = 0
            bear_score = 0

            for d in docs:
                text_lower = d["text"].lower()
                for kw in bullish_keywords:
                    if kw in text_lower:
                        bull_score += 1
                for kw in bearish_keywords:
                    if kw in text_lower:
                        bear_score += 1

                citations.append(
                    Citation(
                        source_id=d["id"],
                        title=d["title"],
                        excerpt=d["text"][:280] + ("..." if len(d["text"]) > 280 else ""),
                        relevance_score=round(d["score"], 3),
                        page_or_section=d.get("section", "N/A"),
                    )
                )
                evidence.append(f"[{d['title']}] {d['text'][:120]}...")

            if bull_score > bear_score + 1:
                signal = SignalLabel.BULLISH
                conf = min(0.82, 0.55 + (bull_score - bear_score) * 0.07)
                reason = f"Retrieved filings show predominantly positive language (bull keywords={bull_score}, bear={bear_score})."
            elif bear_score > bull_score + 1:
                signal = SignalLabel.BEARISH
                conf = min(0.82, 0.55 + (bear_score - bull_score) * 0.07)
                reason = f"Retrieved filings highlight risks and challenges (bear keywords={bear_score}, bull={bull_score})."
            else:
                signal = SignalLabel.NEUTRAL
                conf = 0.58
                reason = f"Mixed signals in filings (bull={bull_score}, bear={bear_score}). No clear directional bias."

            latency = (time.perf_counter() - start) * 1000
            return self._make_output(
                signal=signal,
                confidence=conf,
                reasoning=reason,
                evidence=evidence,
                citations=citations,
                latency_ms=latency,
                metadata={"num_docs": len(docs), "bull_score": bull_score, "bear_score": bear_score},
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return self._degraded(f"Exception in fundamental agent: {str(e)}", latency)