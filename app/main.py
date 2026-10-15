"""
VibeFinance – Interactive Financial Intelligence Dashboard
Run: streamlit run app/main.py
"""
import streamlit as st
import asyncio
import sys
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipeline import VibeFinancePipeline
from app.user.profiles import get_demo_profiles
from app.data.market_data import get_market_snapshot
from app.agents.schemas import SignalLabel

st.set_page_config(
    page_title="VibeFinance | Multi-Agent Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .signal-bullish { color: #00c853; font-weight: 700; }
    .signal-bearish { color: #ff1744; font-weight: 700; }
    .signal-neutral { color: #ffab00; font-weight: 700; }
    .signal-mixed { color: #7c4dff; font-weight: 700; }
    .agent-card { padding: 1rem; border-radius: 0.5rem; border: 1px solid #333; margin-bottom: 0.8rem; }
    .citation { font-size: 0.85rem; background: #1e1e1e; padding: 0.6rem; border-radius: 0.3rem; margin: 0.3rem 0; }
</style>
""", unsafe_allow_html=True)


def signal_color(sig: str) -> str:
    return {
        "bullish": "signal-bullish",
        "bearish": "signal-bearish",
        "neutral": "signal-neutral",
        "mixed": "signal-mixed",
    }.get(sig.lower(), "signal-neutral")


@st.cache_resource
def get_pipeline():
    return VibeFinancePipeline()


def main():
    st.title("📈 VibeFinance")
    st.caption("Multi-Agent Autonomous Financial Intelligence for Retail Investors")

    pipeline = get_pipeline()
    profiles = get_demo_profiles()

    # ── Sidebar ──────────────────────────────────────────────
    with st.sidebar:
        st.header("⚙️ Configuration")
        profile_key = st.selectbox(
            "Investor Profile",
            options=list(profiles.keys()),
            format_func=lambda k: f"{profiles[k].name} ({k})",
        )
        user = profiles[profile_key]

        symbol = st.selectbox(
            "Symbol",
            options=["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"],
        )

        st.divider()
        st.subheader("🧪 Failure Simulation")
        force_rag_fail = st.checkbox("Simulate missing filings (RAG failure)", value=False)
        force_mkt_fail = st.checkbox("Simulate unavailable price feed", value=False)

        run_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True)

        st.divider()
        st.markdown("**User Snapshot**")
        st.write(f"**Risk:** {user.risk_tolerance}")
        st.write(f"**Horizon:** {user.investment_horizon}")
        st.write(f"**Max position:** {user.max_position_pct:.0%}")
        if user.behavioral_notes:
            st.caption("Behavioral notes:")
            for n in user.behavioral_notes:
                st.caption(f"• {n}")

    # ── Main area ────────────────────────────────────────────
    if not run_btn:
        st.info("Select a profile & symbol, then click **Run Analysis** to see the full multi-agent pipeline.")
        st.markdown("""
        ### What this demo shows
        1. **Multi-dimensional signals** – Momentum, Sentiment, Fundamental (RAG)
        2. **Parallel specialized agents** with structured outputs
        3. **Retrieval-augmented analysis** with visible citations
        4. **Personalization** – same market data → different advice by risk profile
        5. **Graceful degradation** when data is missing
        6. **Session metrics** – latency, risk concentration, citation count
        """)
        return

    with st.spinner("Running parallel agents + synthesis..."):
        result = asyncio.run(
            pipeline.run(
                symbol=symbol,
                user=user,
                force_rag_failure=force_rag_fail,
                force_market_failure=force_mkt_fail,
            )
        )

    insight = result["insight"]
    agents = result["agent_outputs"]
    metrics = result["metrics"]
    mkt = result["market_data"]

    # ── Top metrics row ──────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Overall Signal", insight.overall_signal.value.upper())
    c2.metric("Confidence", f"{insight.confidence:.0%}")
    c3.metric("Total Latency", f"{result['total_latency_ms']:.0f} ms")
    c4.metric("Risk Concentration (HHI)", f"{insight.risk_concentration_score or 0:.3f}")
    c5.metric("Citations", metrics.num_citations)

    st.divider()

    # ── Market snapshot ──────────────────────────────────────
    st.subheader(f"📊 Market Snapshot – {symbol}")
    if mkt:
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Last Price", f"₹{mkt.get('last_price', 0):,.2f}", f"{mkt.get('change_1d_pct', 0):+.2f}%")
        mc2.metric("5d Momentum", f"{mkt.get('momentum_5d_pct', 0):+.2f}%")
        mc3.metric("RSI(14)", f"{mkt.get('rsi_14', 0):.1f}")
        mc4.metric("Volume Ratio", f"{mkt.get('volume_ratio', 0):.2f}x")
    else:
        st.warning("⚠️ Price feed unavailable (degraded mode)")

    st.divider()

    # ── Agent cards ──────────────────────────────────────────
    st.subheader("🤖 Multi-Agent Analysis (Parallel)")
    cols = st.columns(len(agents))
    for col, agent in zip(cols, agents):
        with col:
            status_icon = "⚠️" if agent.status.value == "degraded" else "✅"
            st.markdown(f"**{status_icon} {agent.agent_name}**")
            st.markdown(
                f"<span class='{signal_color(agent.signal.value)}'>{agent.signal.value.upper()}</span> "
                f"· conf {agent.confidence:.0%} · {agent.latency_ms:.0f} ms",
                unsafe_allow_html=True,
            )
            st.caption(agent.dimension)
            st.write(agent.reasoning)
            if agent.evidence:
                with st.expander("Evidence"):
                    for e in agent.evidence:
                        st.write(f"• {e}")
            if agent.citations:
                with st.expander(f"Citations ({len(agent.citations)})"):
                    for c in agent.citations:
                        st.markdown(
                            f"<div class='citation'><b>{c.title}</b> (score={c.relevance_score:.2f})<br>"
                            f"<i>{c.excerpt}</i></div>",
                            unsafe_allow_html=True,
                        )

    st.divider()

    # ── Synthesis ────────────────────────────────────────────
    st.subheader("🧠 Synthesized Intelligence (Personalized)")
    st.markdown(f"**For:** {insight.personalized_for}")
    st.markdown(f"**Summary:** {insight.summary}")

    st.markdown("#### Recommendations")
    for r in insight.recommendations:
        st.success(r)

    if insight.risk_warnings:
        st.markdown("#### Risk Warnings")
        for w in insight.risk_warnings:
            st.warning(w)

    if insight.portfolio_impact:
        st.info(f"**Portfolio Impact:** {insight.portfolio_impact}")

    with st.expander("📜 Full Reasoning Chain", expanded=False):
        st.markdown(insight.detailed_reasoning)

    if insight.citations:
        with st.expander("📚 All Source Attributions"):
            for c in insight.citations:
                st.markdown(f"**{c.title}** · relevance {c.relevance_score:.2f} · {c.page_or_section}")
                st.caption(c.excerpt)

    st.divider()

    # ── Portfolio & Watchlist ────────────────────────────────
    st.subheader("💼 Current Portfolio & Watchlist")
    pc1, pc2 = st.columns(2)
    with pc1:
        st.markdown("**Holdings**")
        if user.portfolio:
            for p in user.portfolio:
                val = p.quantity * (p.current_price or p.avg_cost)
                st.write(f"• {p.symbol}: {p.quantity} shares @ ₹{p.avg_cost:.0f} → ₹{val:,.0f} ({p.sector})")
        else:
            st.write("Empty")
    with pc2:
        st.markdown("**Watchlist**")
        for w in user.watchlist:
            st.write(f"• {w}")

    st.divider()

    # ── Metrics panel ────────────────────────────────────────
    st.subheader("📏 Session Metrics")
    mcol1, mcol2, mcol3 = st.columns(3)
    mcol1.write("**Agent Latencies (ms)**")
    for name, lat in metrics.agent_latencies.items():
        mcol1.write(f"• {name}: {lat:.0f}")
    mcol2.metric("Signal Accuracy Proxy", f"{metrics.signal_accuracy_proxy:.1%}" if metrics.signal_accuracy_proxy else "N/A")
    mcol3.write("**Degraded Agents**")
    if metrics.degraded_agents:
        for d in metrics.degraded_agents:
            mcol3.error(d)
    else:
        mcol3.success("None")

    st.caption(f"Session ID: {metrics.session_id} · Logged to data/metrics/sessions.jsonl")


if __name__ == "__main__":
    main()