"""
End-to-end orchestration: data → parallel agents → synthesis → metrics
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
    ) -> Dict[str, Any]:
        """
        Full pipeline from raw data → multi-agent → personalized insight
        """
        t0 = time.perf_counter()

        # 1. Ingest data
        market_data = {} if force_market_failure else get_market_snapshot([symbol])
        sentiment_data = get_sentiment_snapshot([symbol])
        company_name = get_company_name(symbol)

        context = {
            "symbol": symbol,
            "company_name": company_name,
            "market_data": market_data,
            "sentiment_data": sentiment_data,
            "force_rag_failure": force_rag_failure,
            "user": user,
        }

        # 2. Run specialized agents in parallel
        results = await asyncio.gather(
            self.momentum.run(context),
            self.sentiment.run(context),
            self.fundamental.run(context),
            return_exceptions=True,
        )

        agent_outputs: list[AgentOutput] = []
        for r in results:
            if isinstance(r, Exception):
                print(f"[WARN] Agent raised exception: {r}")
                continue
            agent_outputs.append(r)

        # 3. Synthesis + personalization
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
            # Create a minimal fallback insight so the pipeline never returns None
            insight = SynthesizedInsight(
                overall_signal=SignalLabel.NEUTRAL,
                confidence=0.3,
                summary="Synthesis failed – using neutral fallback.",
                detailed_reasoning=f"Error during synthesis: {e}",
                recommendations=["Unable to generate recommendation due to internal error."],
                risk_warnings=["Treat this output with caution."],
                agent_outputs=agent_outputs,
                citations=[],
                personalized_for=f"{user.name} ({user.risk_tolerance})",
                portfolio_impact=None,
                risk_concentration_score=0.0,
            )

        total_latency = (time.perf_counter() - t0) * 1000

        # 4. Metrics
        session_metrics = self.metrics.log_session(
            user_id=user.user_id,
            symbol=symbol,
            agent_outputs=agent_outputs,
            insight=insight,
            total_latency_ms=total_latency,
        )

        return {
            "insight": insight,
            "agent_outputs": agent_outputs,
            "metrics": session_metrics,
            "market_data": market_data.get(symbol, {}),
            "total_latency_ms": total_latency,
        }