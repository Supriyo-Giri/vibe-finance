"""
End-to-end orchestration: real data → parallel agents → synthesis → metrics
"""
import asyncio
import time
from typing import Dict, Any, Optional
from app.agents.momentum_agent import MomentumAgent
from app.agents.sentiment_agent import SentimentAgent
from app.agents.fundamental_agent import FundamentalAgent
from app.agents.synthesis_agent import SynthesisAgent
from app.agents.schemas import UserProfile, SynthesizedInsight, AgentOutput, SignalLabel
from app.data.market_data import get_market_snapshot, get_sentiment_snapshot, get_company_name
from app.metrics.logger import MetricsLogger
from app.rag.retriever import DocumentRetriever


class VibeFinancePipeline:
    def __init__(self):
        self.retriever = DocumentRetriever()
        self.momentum = MomentumAgent()
        self.sentiment = SentimentAgent()
        self.fundamental = FundamentalAgent(retriever=self.retriever)
        self.synthesis = SynthesisAgent()
        self.metrics = MetricsLogger()

    async def run(
        self,
        symbol: str,
        user: UserProfile,
        force_rag_failure: bool = False,
        force_market_failure: bool = False,
        use_live: bool = True,
    ) -> Dict[str, Any]:
        t0 = time.perf_counter()

        if force_market_failure:
            market_data = {}
        else:
            market_data = get_market_snapshot([symbol], use_live=use_live)

        sentiment_data = get_sentiment_snapshot([symbol], market_data=market_data)
        company_name = (
            market_data.get(symbol, {}).get("company_name")
            or get_company_name(symbol)
        )

        context = {
            "symbol": symbol,
            "company_name": company_name,
            "market_data": market_data,
            "sentiment_data": sentiment_data,
            "force_rag_failure": force_rag_failure,
            "user": user,
        }

        results = await asyncio.gather(
            self.momentum.run(context),
            self.sentiment.run(context),
            self.fundamental.run(context),
            return_exceptions=True,
        )

        agent_outputs: list[AgentOutput] = []
        for r in results:
            if isinstance(r, Exception):
                print(f"[WARN] Agent exception: {r}")
                continue
            agent_outputs.append(r)

        insight = None
        try:
            insight = await self.synthesis.synthesize(
                agent_outputs=agent_outputs,
                user=user,
                symbol=symbol,
                market_data=market_data,
            )
        except Exception as e:
            print(f"[ERROR] Synthesis failed: {e}")
            insight = SynthesizedInsight(
                overall_signal=SignalLabel.NEUTRAL,
                confidence=0.3,
                summary="Synthesis failed – neutral fallback.",
                detailed_reasoning=f"Error: {e}",
                recommendations=["Unable to generate recommendation."],
                risk_warnings=["Treat with caution."],
                agent_outputs=agent_outputs,
                citations=[],
                personalized_for=f"{user.name} ({user.risk_tolerance})",
                portfolio_impact=None,
                risk_concentration_score=0.0,
            )

        total_latency = (time.perf_counter() - t0) * 1000

        session_metrics = self.metrics.log_session(
            user_id=user.user_id,
            symbol=symbol,
            agent_outputs=agent_outputs,
            insight=insight,
            total_latency_ms=total_latency,
        )

        mkt = market_data.get(symbol, {})
        return {
            "insight": insight,
            "agent_outputs": agent_outputs,
            "metrics": session_metrics,
            "market_data": mkt,
            "total_latency_ms": total_latency,
            "data_source": mkt.get("source", "unknown"),
        }