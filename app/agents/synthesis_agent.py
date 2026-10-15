"""
Synthesis Agent – merges parallel agent outputs + personalizes for the user
"""
import time
from typing import Any, Dict, List
from app.agents.base import BaseAgent, MockLLM
from app.agents.schemas import (
    AgentOutput,
    SynthesizedInsight,
    SignalLabel,
    Citation,
    UserProfile,
)


class SynthesisAgent(BaseAgent):
    name = "SynthesisAgent"
    dimension = "synthesis"

    async def run(self, context: Dict[str, Any]) -> AgentOutput:
        """Not used directly – call synthesize() instead."""
        return self._make_output(
            signal=SignalLabel.NEUTRAL,
            confidence=0.0,
            reasoning="Use synthesize() method instead of run().",
        )

    async def synthesize(
        self,
        agent_outputs: List[AgentOutput],
        user: UserProfile,
        symbol: str,
        market_data: Dict[str, Any],
    ) -> SynthesizedInsight:
        start = time.perf_counter()

        # Collect signals
        signal_dicts = [
            {"signal": o.signal.value, "confidence": o.confidence, "agent": o.agent_name}
            for o in agent_outputs
            if o.status.value != "failed"
        ]

        mock = MockLLM.synthesize(signal_dicts, user.risk_tolerance)

        overall = SignalLabel(mock["overall_signal"])
        conf = mock["confidence"]

        # Build detailed reasoning chain
        lines = [
            f"**Multi-Agent Consensus for {symbol}**",
            f"User profile: {user.name} ({user.risk_tolerance} risk, {user.investment_horizon} horizon)",
            "",
            "### Individual Agent Views",
        ]
        for o in agent_outputs:
            status_flag = " ⚠️ DEGRADED" if o.status.value == "degraded" else ""
            lines.append(
                f"- **{o.agent_name}** ({o.dimension}): {o.signal.value.upper()} "
                f"(conf={o.confidence:.0%}){status_flag}"
            )
            lines.append(f"  Reasoning: {o.reasoning}")
            if o.evidence:
                lines.append(f"  Evidence: {'; '.join(o.evidence[:2])}")
            lines.append("")

        lines.append("### Synthesis")
        lines.append(mock["summary"])
        lines.append(mock["size_language"])
        lines.append("")
        lines.append(f"**Risk note for {user.risk_tolerance} profile:** {mock['risk_warning']}")

        # Portfolio impact
        portfolio_impact = None
        risk_score = 0.0
        if user.portfolio:
            total_value = sum(p.quantity * (p.current_price or p.avg_cost) for p in user.portfolio)
            if total_value > 0:
                weights = []
                for p in user.portfolio:
                    val = p.quantity * (p.current_price or p.avg_cost)
                    weights.append(val / total_value)
                risk_score = sum(w ** 2 for w in weights)  # HHI
                holding = next(
                    (p for p in user.portfolio if p.symbol == symbol or p.symbol.startswith(symbol.split(".")[0])),
                    None,
                )
                if holding:
                    portfolio_impact = (
                        f"You already hold {holding.quantity} shares of {holding.symbol}. "
                        f"Current weight ≈ {(holding.quantity * (holding.current_price or holding.avg_cost) / total_value):.1%}."
                    )
                else:
                    portfolio_impact = (
                        f"No current holding in {symbol}. Adding it would change concentration "
                        f"(current HHI={risk_score:.3f})."
                    )

        # Collect all citations
        all_citations: List[Citation] = []
        for o in agent_outputs:
            all_citations.extend(o.citations)

        recommendations = []
        if overall == SignalLabel.BULLISH:
            recommendations.append(mock["size_language"])
            recommendations.append("Monitor volume confirmation and any upcoming earnings date.")
        elif overall == SignalLabel.BEARISH:
            recommendations.append("Reduce exposure or avoid new long positions until clarity improves.")
            recommendations.append("Set strict stop-loss if already holding.")
        else:
            # Personalize even the "mixed" case
            recommendations.append(mock["size_language"])
            if user.risk_tolerance == "conservative":
                recommendations.append("Prefer waiting for clearer multi-agent alignment before acting.")
            elif user.risk_tolerance == "aggressive":
                recommendations.append("You may take a small tactical position while keeping strict risk controls.")
            else:
                recommendations.append("Wait for alignment across technical, sentiment and fundamental agents.")

        risk_warnings = [mock["risk_warning"]]
        if risk_score > 0.25:
            risk_warnings.append(
                f"Portfolio concentration is elevated (HHI={risk_score:.3f}). Diversification recommended."
            )

        degraded = [o.agent_name for o in agent_outputs if o.status.value == "degraded"]
        if degraded:
            risk_warnings.append(
                f"Some agents ran in degraded mode: {', '.join(degraded)}. Treat conclusions with extra caution."
            )

        detailed = "\n".join(lines)

        return SynthesizedInsight(
            overall_signal=overall,
            confidence=conf,
            summary=mock["summary"],
            detailed_reasoning=detailed,
            recommendations=recommendations,
            risk_warnings=risk_warnings,
            agent_outputs=agent_outputs,
            citations=all_citations,
            personalized_for=f"{user.name} ({user.risk_tolerance})",
            portfolio_impact=portfolio_impact,
            risk_concentration_score=round(risk_score, 4),
        )