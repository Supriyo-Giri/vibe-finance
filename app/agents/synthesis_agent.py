"""
Synthesis Agent – merges agent outputs + personalizes.
Uses real LLM when API key is set; otherwise MockLLM.
"""
from typing import Any, Dict, List
from app.agents.base import BaseAgent, MockLLM
from app.agents.schemas import (
    AgentOutput,
    SynthesizedInsight,
    SignalLabel,
    Citation,
    UserProfile,
)
from app.agents.llm_client import llm_available, chat_json


class SynthesisAgent(BaseAgent):
    name = "SynthesisAgent"
    dimension = "synthesis"

    async def run(self, context: Dict[str, Any]) -> AgentOutput:
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
        if llm_available():
            ai = self._ai_synthesize(agent_outputs, user, symbol, market_data)
            if ai is not None:
                return ai
        return self._mock_synthesize(agent_outputs, user, symbol, market_data)

    def _ai_synthesize(
        self,
        agent_outputs: List[AgentOutput],
        user: UserProfile,
        symbol: str,
        market_data: Dict[str, Any],
    ) -> SynthesizedInsight | None:
        agents_blob = []
        all_citations: List[Citation] = []
        for o in agent_outputs:
            all_citations.extend(o.citations)
            agents_blob.append({
                "agent": o.agent_name,
                "dimension": o.dimension,
                "signal": o.signal.value,
                "confidence": o.confidence,
                "status": o.status.value,
                "reasoning": o.reasoning,
                "evidence": o.evidence[:4],
                "citations": [
                    {"title": c.title, "excerpt": c.excerpt[:200], "score": c.relevance_score}
                    for c in o.citations[:2]
                ],
            })

        mkt = market_data.get(symbol, {}) if isinstance(market_data, dict) else {}
        if not isinstance(mkt, dict):
            mkt = {}
        # If market_data is already the single-symbol dict
        if not mkt and market_data and "last_price" in market_data:
            mkt = market_data

        portfolio_lines = []
        risk_score = 0.0
        portfolio_impact = None
        if user.portfolio:
            total_value = sum(p.quantity * (p.current_price or p.avg_cost) for p in user.portfolio)
            if total_value > 0:
                weights = []
                for p in user.portfolio:
                    val = p.quantity * (p.current_price or p.avg_cost)
                    weights.append(val / total_value)
                    portfolio_lines.append(
                        f"{p.symbol}: {p.quantity} shares, weight {val/total_value:.1%}, sector {p.sector}"
                    )
                risk_score = sum(w ** 2 for w in weights)
                holding = next(
                    (
                        p for p in user.portfolio
                        if p.symbol == symbol or p.symbol.startswith(symbol.split(".")[0])
                    ),
                    None,
                )
                if holding:
                    w = holding.quantity * (holding.current_price or holding.avg_cost) / total_value
                    portfolio_impact = (
                        f"You already hold {holding.quantity} shares of {holding.symbol}. "
                        f"Current weight ≈ {w:.1%}."
                    )
                else:
                    portfolio_impact = (
                        f"No current holding in {symbol}. Current portfolio HHI={risk_score:.3f}."
                    )

        system = (
            "You are a careful Indian retail investment research assistant. "
            "You synthesize multi-agent market analysis into clear, personalized guidance. "
            "You are NOT a SEBI-registered advisor; phrase recommendations as research insights, not orders. "
            "Respect the investor's risk tolerance strictly. "
            "Ground claims in the agent evidence and citations provided. "
            "Return JSON with keys: overall_signal (bullish|bearish|neutral|mixed), "
            "confidence (0-1 float), summary (1-2 sentences), "
            "detailed_reasoning (markdown, short), "
            "recommendations (array of 2-4 concrete strings), "
            "risk_warnings (array of 1-3 strings)."
        )

        user_prompt = (
            f"Symbol: {symbol}\n"
            f"Market snapshot: last={mkt.get('last_price')}, change_1d%={mkt.get('change_1d_pct')}, "
            f"momentum_5d%={mkt.get('momentum_5d_pct')}, RSI={mkt.get('rsi_14')}, "
            f"vol_ratio={mkt.get('volume_ratio')}\n\n"
            f"Investor:\n"
            f"- Name: {user.name}\n"
            f"- Risk tolerance: {user.risk_tolerance}\n"
            f"- Horizon: {user.investment_horizon}\n"
            f"- Max position: {user.max_position_pct:.0%}\n"
            f"- Behavioral notes: {user.behavioral_notes}\n"
            f"- Portfolio: {portfolio_lines or ['empty']}\n"
            f"- Portfolio HHI: {risk_score:.3f}\n\n"
            f"Agent outputs (JSON):\n{agents_blob}\n\n"
            "Return personalized synthesis JSON."
        )

        data = chat_json(system, user_prompt)
        if not data:
            return None

        try:
            sig = str(data.get("overall_signal", "neutral")).lower()
            if sig not in ("bullish", "bearish", "neutral", "mixed"):
                sig = "mixed"
            conf = float(data.get("confidence", 0.5))
            conf = max(0.0, min(1.0, conf))

            recs = data.get("recommendations") or []
            if isinstance(recs, str):
                recs = [recs]
            warns = data.get("risk_warnings") or []
            if isinstance(warns, str):
                warns = [warns]

            if risk_score > 0.25 and not any(
                "HHI" in str(w) or "concentration" in str(w).lower() for w in warns
            ):
                warns.append(
                    f"Portfolio concentration is elevated (HHI={risk_score:.3f}). Diversification recommended."
                )

            degraded = [o.agent_name for o in agent_outputs if o.status.value == "degraded"]
            if degraded:
                warns.append(
                    f"Some agents ran in degraded mode: {', '.join(degraded)}. Extra caution advised."
                )

            detailed = data.get("detailed_reasoning") or data.get("summary") or ""
            lines = [str(detailed), "", "### Agent inputs used"]
            for o in agent_outputs:
                flag = " (DEGRADED)" if o.status.value == "degraded" else ""
                lines.append(
                    f"- **{o.agent_name}**{flag}: {o.signal.value} @ {o.confidence:.0%} — {o.reasoning}"
                )
            detailed = "\n".join(lines)

            return SynthesizedInsight(
                overall_signal=SignalLabel(sig),
                confidence=conf,
                summary=str(data.get("summary", "AI synthesis complete.")),
                detailed_reasoning=detailed,
                recommendations=[str(r) for r in recs][:5] or ["No clear action — wait for alignment."],
                risk_warnings=[str(w) for w in warns][:5],
                agent_outputs=agent_outputs,
                citations=all_citations,
                personalized_for=f"{user.name} ({user.risk_tolerance})",
                portfolio_impact=portfolio_impact,
                risk_concentration_score=round(risk_score, 4),
            )
        except Exception as e:
            print(f"[SynthesisAgent] AI parse failed: {e}")
            return None

    def _mock_synthesize(
        self,
        agent_outputs: List[AgentOutput],
        user: UserProfile,
        symbol: str,
        market_data: Dict[str, Any],
    ) -> SynthesizedInsight:
        signal_dicts = [
            {"signal": o.signal.value, "confidence": o.confidence, "agent": o.agent_name}
            for o in agent_outputs
            if o.status.value != "failed"
        ]
        mock = MockLLM.synthesize(
            signal_dicts,
            user.risk_tolerance,
            symbol=symbol,
            agents_detail=signal_dicts,
        )
        overall = SignalLabel(mock["overall_signal"])
        conf = mock["confidence"]

        lines = [
            f"**Multi-Agent Consensus for {symbol}**",
            f"Investor: {user.name} · {user.risk_tolerance} risk · {user.investment_horizon} horizon",
            "",
            "### Individual Agent Views",
        ]
        for o in agent_outputs:
            status_flag = " ⚠️ DEGRADED" if o.status.value == "degraded" else ""
            lines.append(
                f"- **{o.agent_name}** ({o.dimension}): {o.signal.value.upper()} "
                f"(conf={o.confidence:.0%}){status_flag}"
            )
            lines.append(f"  {o.reasoning}")
            if o.evidence:
                lines.append(f"  Evidence: {'; '.join(o.evidence[:2])}")
            lines.append("")

        lines.append("### Synthesis")
        lines.append(mock["summary"])
        lines.append("")
        lines.append(f"**Risk note:** {mock['risk_warning']}")

        portfolio_impact = None
        risk_score = 0.0
        if user.portfolio:
            total_value = sum(p.quantity * (p.current_price or p.avg_cost) for p in user.portfolio)
            if total_value > 0:
                weights = [
                    (p.quantity * (p.current_price or p.avg_cost)) / total_value
                    for p in user.portfolio
                ]
                risk_score = sum(w ** 2 for w in weights)
                holding = next(
                    (
                        p for p in user.portfolio
                        if p.symbol == symbol or p.symbol.startswith(symbol.split(".")[0])
                    ),
                    None,
                )
                if holding:
                    w = holding.quantity * (holding.current_price or holding.avg_cost) / total_value
                    portfolio_impact = (
                        f"You already own {holding.quantity:.0f} shares of {holding.symbol.replace('.NS','')} "
                        f"(≈{w:.1%} of portfolio). Adding more would push single-name concentration higher."
                    )
                else:
                    portfolio_impact = (
                        f"You do not currently hold {symbol.replace('.NS','')}. "
                        f"Current portfolio concentration (HHI) is {risk_score:.3f}."
                    )

        all_citations: List[Citation] = []
        for o in agent_outputs:
            all_citations.extend(o.citations)

        recommendations = mock.get("recommendations", [])
        risk_warnings = [mock["risk_warning"]]
        if risk_score > 0.28:
            risk_warnings.append(
                f"Portfolio is concentrated (HHI={risk_score:.3f}). "
                f"Any new position in {symbol.replace('.NS','')} should be sized carefully to avoid further clustering."
            )
        degraded = [o.agent_name for o in agent_outputs if o.status.value == "degraded"]
        if degraded:
            risk_warnings.append(
                f"Note: {', '.join(degraded)} ran in degraded mode. Treat the overall view with extra caution."
            )

        if user.behavioral_notes and overall == SignalLabel.BULLISH:
            note = user.behavioral_notes[0]
            if "sold winners" in note.lower() or "early" in note.lower():
                recommendations.append(
                    "Reminder from your own history: you tend to exit winners early. "
                    "Decide the profit-taking plan before entry."
                )

        return SynthesizedInsight(
            overall_signal=overall,
            confidence=conf,
            summary=mock["summary"],
            detailed_reasoning="\n".join(lines),
            recommendations=recommendations,
            risk_warnings=risk_warnings,
            agent_outputs=agent_outputs,
            citations=all_citations,
            personalized_for=f"{user.name} ({user.risk_tolerance})",
            portfolio_impact=portfolio_impact,
            risk_concentration_score=round(risk_score, 4),
        )