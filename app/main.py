"""
VibeFinance – Multi-Agent Autonomous Financial Intelligence
Professional Black & White Dashboard
Run: streamlit run app/main.py
"""
import streamlit as st
import asyncio
import time
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipeline import VibeFinancePipeline
from app.user.profiles import get_demo_profiles
from app.config import settings

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

st.set_page_config(
    page_title="VibeFinance | Multi-Agent Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
.stApp {
    background: #0a0a0a;
    color: #f5f5f5;
}
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1280px;
}
h1, h2, h3, h4 {
    color: #ffffff !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em;
}
h1 { font-size: 1.75rem !important; }
h2 { font-size: 1.25rem !important; margin-top: 1.5rem !important; }
h3 { font-size: 1.05rem !important; }

section[data-testid="stSidebar"] {
    background: #111111 !important;
    border-right: 1px solid #222222;
}
section[data-testid="stSidebar"] * {
    color: #e5e5e5 !important;
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stCheckbox label,
section[data-testid="stSidebar"] .stToggle label {
    color: #a3a3a3 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.stButton > button {
    background: #ffffff !important;
    color: #0a0a0a !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.03em;
    padding: 0.6rem 1.2rem !important;
    transition: all 0.15s ease;
}
.stButton > button:hover {
    background: #e5e5e5 !important;
    box-shadow: 0 0 0 1px #ffffff;
}

div[data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 600 !important; }
div[data-testid="stMetricLabel"] {
    color: #a3a3a3 !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.kpi-card {
    background: #141414;
    border: 1px solid #262626;
    border-radius: 8px;
    padding: 16px 18px;
    text-align: center;
    height: 100%;
}
.kpi-label {
    color: #737373;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 500;
}
.kpi-value {
    color: #fafafa;
    font-size: 1.4rem;
    font-weight: 700;
    margin-top: 6px;
    letter-spacing: -0.02em;
}

.signal-bullish { color: #ffffff; font-weight: 700; }
.signal-bearish { color: #a3a3a3; font-weight: 700; }
.signal-neutral { color: #d4d4d4; font-weight: 700; }
.signal-mixed   { color: #e5e5e5; font-weight: 700; }

.console-box {
    background: #0c0c0c;
    border: 1px solid #262626;
    border-radius: 8px;
    padding: 14px 16px;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 0.78rem;
    color: #a3a3a3;
    max-height: 260px;
    overflow-y: auto;
    line-height: 1.6;
}
.console-ok   { color: #e5e5e5; }
.console-warn { color: #a3a3a3; }
.console-err  { color: #737373; }
.console-info { color: #d4d4d4; }
.console-dim  { color: #525252; }

.agent-card {
    background: #141414;
    border: 1px solid #262626;
    border-radius: 8px;
    padding: 16px;
    height: 100%;
}
.agent-card-header {
    font-weight: 600;
    font-size: 0.9rem;
    color: #fafafa;
    margin-bottom: 8px;
}
.agent-meta {
    font-size: 0.75rem;
    color: #737373;
    margin-bottom: 10px;
}

.citation {
    font-size: 0.8rem;
    background: #0c0c0c;
    border-left: 2px solid #525252;
    padding: 10px 12px;
    border-radius: 0 6px 6px 0;
    margin: 6px 0;
    color: #d4d4d4;
    line-height: 1.5;
}

.streamlit-expanderHeader {
    background: #141414 !important;
    color: #e5e5e5 !important;
    border: 1px solid #262626 !important;
    border-radius: 6px !important;
}

hr {
    border: none;
    border-top: 1px solid #262626;
    margin: 1.5rem 0;
}

div[data-testid="stAlert"] {
    background: #141414 !important;
    border: 1px solid #262626 !important;
    color: #e5e5e5 !important;
    border-radius: 6px !important;
}

.stSelectbox > div > div {
    background: #141414 !important;
    border: 1px solid #333333 !important;
    color: #f5f5f5 !important;
}

.stCaption, small { color: #737373 !important; }

.footer {
    text-align: center;
    color: #525252;
    font-size: 0.75rem;
    margin-top: 2.5rem;
    padding-top: 1rem;
    border-top: 1px solid #1a1a1a;
}
</style>
""", unsafe_allow_html=True)


def signal_class(sig: str) -> str:
    return {
        "bullish": "signal-bullish",
        "bearish": "signal-bearish",
        "neutral": "signal-neutral",
        "mixed": "signal-mixed",
    }.get(sig.lower(), "signal-neutral")


def signal_badge(sig: str) -> str:
    return {
        "bullish": "▲ BULLISH",
        "bearish": "▼ BEARISH",
        "neutral": "● NEUTRAL",
        "mixed": "◆ MIXED",
    }.get(sig.lower(), "● NEUTRAL")


@st.cache_resource
def get_pipeline():
    return VibeFinancePipeline()


def make_price_chart(symbol: str, history: list, dates: list):
    if not HAS_PLOTLY or not history:
        return None
    if not dates or len(dates) != len(history):
        dates = [str(i) for i in range(len(history))]
    color = "#ffffff" if history[-1] >= history[0] else "#a3a3a3"
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=history, mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor="rgba(255,255,255,0.04)" if color == "#ffffff" else "rgba(163,163,163,0.04)",
        name=symbol,
    ))
    fig.update_layout(
        height=260, margin=dict(l=10, r=10, t=36, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#737373", size=11, family="Inter"),
        title=dict(text=f"{symbol.replace('.NS','')} · Price", font=dict(size=13, color="#e5e5e5")),
        xaxis=dict(showgrid=False, zeroline=False, nticks=7, color="#525252"),
        yaxis=dict(showgrid=True, gridcolor="#1a1a1a", zeroline=False, tickprefix="₹", color="#525252"),
        showlegend=False,
    )
    return fig


def make_confidence_bars(agents):
    if not HAS_PLOTLY:
        return None
    names = [a.agent_name.replace("Agent", "") for a in agents]
    confs = [a.confidence * 100 for a in agents]
    colors = ["#ffffff" if a.signal.value == "bullish" else
              "#a3a3a3" if a.signal.value == "bearish" else "#d4d4d4"
              for a in agents]
    fig = go.Figure(go.Bar(
        x=confs, y=names, orientation="h",
        marker=dict(color=colors),
        text=[f"{c:.0f}%" for c in confs],
        textposition="inside", insidetextanchor="middle",
        textfont=dict(color="#0a0a0a", size=12, family="Inter"),
    ))
    fig.update_layout(
        height=180, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#737373", size=11, family="Inter"),
        title=dict(text="Agent Confidence", font=dict(size=13, color="#e5e5e5")),
        xaxis=dict(range=[0, 100], showgrid=True, gridcolor="#1a1a1a", ticksuffix="%"),
        yaxis=dict(showgrid=False),
    )
    return fig


def make_latency_bars(metrics):
    if not HAS_PLOTLY or not metrics.agent_latencies:
        return None
    names = list(metrics.agent_latencies.keys())
    vals = list(metrics.agent_latencies.values())
    fig = go.Figure(go.Bar(
        x=names, y=vals, marker=dict(color="#d4d4d4"),
        text=[f"{v:.0f} ms" for v in vals], textposition="outside",
        textfont=dict(color="#a3a3a3", size=11),
    ))
    fig.update_layout(
        height=200, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#737373", size=11, family="Inter"),
        title=dict(text="Agent Latency (ms)", font=dict(size=13, color="#e5e5e5")),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#1a1a1a"),
        showlegend=False,
    )
    return fig


def make_portfolio_pie(user):
    if not HAS_PLOTLY or not user.portfolio:
        return None
    labels = [p.symbol.replace(".NS", "") for p in user.portfolio]
    values = [p.quantity * (p.current_price or p.avg_cost) for p in user.portfolio]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.58,
        marker=dict(colors=["#ffffff", "#d4d4d4", "#a3a3a3", "#737373", "#525252"]),
        textinfo="label+percent", textfont=dict(size=11, color="#0a0a0a"),
    ))
    fig.update_layout(
        height=230, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#a3a3a3", size=11, family="Inter"),
        title=dict(text="Portfolio Allocation", font=dict(size=13, color="#e5e5e5")),
        showlegend=False,
    )
    return fig


def make_gauge(confidence: float, signal: str):
    if not HAS_PLOTLY:
        return None
    color = "#ffffff" if signal == "bullish" else "#a3a3a3" if signal == "bearish" else "#d4d4d4"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=confidence * 100,
        number=dict(suffix="%", font=dict(size=28, color="#fafafa", family="Inter")),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor="#333333"),
            bar=dict(color=color),
            bgcolor="#141414",
            borderwidth=0,
            steps=[
                dict(range=[0, 40], color="#1a1a1a"),
                dict(range=[40, 70], color="#262626"),
                dict(range=[70, 100], color="#333333"),
            ],
        ),
        title=dict(text="Consensus Confidence", font=dict(size=13, color="#a3a3a3")),
    ))
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def log_line(kind: str, msg: str) -> str:
    ts = datetime.now().strftime("%H:%M:%S")
    cls = {"ok": "console-ok", "warn": "console-warn", "err": "console-err", "info": "console-info"}.get(kind, "console-dim")
    return f'<span class="console-dim">[{ts}]</span> <span class="{cls}">{msg}</span>'


def main():
    st.markdown("## VibeFinance")
    st.caption("Multi-agent autonomous financial intelligence · Real market data · RAG · Personalization")

    pipeline = get_pipeline()
    profiles = get_demo_profiles()

    with st.sidebar:
        st.markdown("### Control Panel")
        st.markdown("")
        profile_key = st.selectbox(
            "Investor Profile",
            options=list(profiles.keys()),
            format_func=lambda k: f"{profiles[k].name}  ·  {k.capitalize()}",
        )
        user = profiles[profile_key]
        symbol = st.selectbox(
            "Symbol",
            options=["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"],
        )
        use_live = st.toggle("Live market data (yfinance)", value=True)
        st.markdown("---")
        st.markdown("### Failure Injection")
        force_rag_fail = st.checkbox("Missing filings (RAG fail)", value=False)
        force_mkt_fail = st.checkbox("Price feed down", value=False)
        st.markdown("---")
        def main():
            st.markdown("""
                <style>
                section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
                    color: black !important;
                }
                </style>
            """, unsafe_allow_html=True)

            st.markdown("## VibeFinance")
            st.caption("Multi-agent autonomous financial intelligence · Real market data · RAG · Personalization")

        # Keep the rest of your existing code unchanged
        run_btn = st.button("RUN MULTI-AGENT ANALYSIS", type="primary", use_container_width=True)
        st.markdown("---")
        st.markdown(f"**{user.name}**")
        st.caption(f"Risk · {user.risk_tolerance}  ·  Horizon · {user.investment_horizon}")
        st.caption(f"Max position · {user.max_position_pct:.0%}")
        for n in user.behavioral_notes:
            st.caption(f"• {n}")
        st.markdown("---")
        st.caption(f"LLM mode: {'mock' if settings.use_mock_llm else settings.llm_model}")
        st.caption("Data: yfinance NSE · RAG: synthetic filings")

    if not run_btn:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown('<div class="kpi-card"><div class="kpi-label">Agents</div><div class="kpi-value">3 Parallel</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="kpi-card"><div class="kpi-label">Data</div><div class="kpi-value">Live + Simulated</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="kpi-card"><div class="kpi-label">Analytics</div><div class="kpi-value">RSI · Momentum · RAG</div></div>', unsafe_allow_html=True)
        st.markdown("")
        st.info("Select an investor profile and symbol, then click **RUN MULTI-AGENT ANALYSIS**.")
        st.markdown("""
**Pipeline overview**
1. Fetch real OHLCV from Yahoo Finance (NSE `.NS` symbols)  
2. Compute RSI(14), 5-day momentum, volume ratio  
3. Sentiment from headline keyword model  
4. RAG over synthetic SEBI / earnings corpus with source attribution  
5. Personalized synthesis based on risk profile & portfolio  
""")
        st.markdown('<div class="footer">VibeFinance · PS 04 · Multi-Agent Financial Intelligence</div>', unsafe_allow_html=True)
        return

    st.markdown("### Agent Console")
    console_placeholder = st.empty()
    logs = []

    def refresh_console():
        console_placeholder.markdown('<div class="console-box">' + "<br>".join(logs) + "</div>", unsafe_allow_html=True)

    logs.append(log_line("info", f"Session · user={user.name} · symbol={symbol} · live={use_live}"))
    logs.append(log_line("info", "Fetching market data..."))
    refresh_console()
    time.sleep(0.25)

    if force_mkt_fail:
        logs.append(log_line("warn", "Price feed forced OFF – MomentumAgent will degrade"))
    else:
        logs.append(log_line("ok", "Requesting yfinance OHLCV + indicators..." if use_live else "Using simulated snapshot"))
    if force_rag_fail:
        logs.append(log_line("warn", "Filings disabled – FundamentalAgent will degrade"))
    else:
        logs.append(log_line("ok", "RAG corpus ready"))
    refresh_console()
    time.sleep(0.2)

    logs.append(log_line("info", "Dispatching MomentumAgent · SentimentAgent · FundamentalAgent"))
    refresh_console()
    for name in ["MomentumAgent", "SentimentAgent", "FundamentalAgent"]:
        logs.append(log_line("info", f"→ {name} started"))
        refresh_console()
        time.sleep(0.15)

    with st.spinner("Agents running..."):
        result = asyncio.run(
            pipeline.run(
                symbol=symbol,
                user=user,
                force_rag_failure=force_rag_fail,
                force_market_failure=force_mkt_fail,
                use_live=use_live and not force_mkt_fail,
            )
        )

    insight = result["insight"]
    agents = result["agent_outputs"]
    metrics = result["metrics"]
    mkt = result["market_data"]
    data_source = result.get("data_source", "unknown")

    for a in agents:
        if a.status.value == "degraded":
            logs.append(log_line("warn", f"✓ {a.agent_name} DEGRADED · {a.signal.value.upper()} ({a.confidence:.0%}) · {a.latency_ms:.0f}ms"))
        else:
            logs.append(log_line("ok", f"✓ {a.agent_name} · {a.signal.value.upper()} ({a.confidence:.0%}) · {a.latency_ms:.0f}ms"))
        refresh_console()
        time.sleep(0.1)

    logs.append(log_line("info", "SynthesisAgent · personalizing for risk profile..."))
    refresh_console()
    time.sleep(0.2)
    logs.append(log_line("ok", f"Consensus {insight.overall_signal.value.upper()} · conf {insight.confidence:.0%} · {result['total_latency_ms']:.0f}ms · data={data_source}"))
    logs.append(log_line("ok", "Pipeline complete"))
    refresh_console()

    st.markdown("---")

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Signal</div><div class="kpi-value"><span class="{signal_class(insight.overall_signal.value)}">{signal_badge(insight.overall_signal.value)}</span></div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Confidence</div><div class="kpi-value">{insight.confidence:.0%}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Latency</div><div class="kpi-value">{result["total_latency_ms"]:.0f} ms</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Risk HHI</div><div class="kpi-value">{(insight.risk_concentration_score or 0):.3f}</div></div>', unsafe_allow_html=True)
    with k5:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Data Source</div><div class="kpi-value" style="font-size:1.1rem">{data_source}</div></div>', unsafe_allow_html=True)

    st.markdown("")

    left, right = st.columns([1.5, 1])
    with left:
        history = mkt.get("history", []) or []
        dates = mkt.get("history_dates", []) or []
        fig_price = make_price_chart(symbol, history, dates)
        if fig_price:
            st.plotly_chart(fig_price, use_container_width=True)
        if mkt:
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("Last", f"₹{mkt.get('last_price', 0):,.2f}", f"{mkt.get('change_1d_pct', 0):+.2f}%")
            mc2.metric("5d Mom", f"{mkt.get('momentum_5d_pct', 0):+.2f}%")
            mc3.metric("RSI(14)", f"{mkt.get('rsi_14', 0):.1f}")
            mc4.metric("Vol Ratio", f"{mkt.get('volume_ratio', 0):.2f}x")
        else:
            st.warning("Price feed unavailable — MomentumAgent degraded")
    with right:
        fig_gauge = make_gauge(insight.confidence, insight.overall_signal.value)
        if fig_gauge:
            st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("---")
    st.markdown("### Agent Results")
    cols = st.columns(len(agents) if agents else 1)
    for col, agent in zip(cols, agents):
        with col:
            status_icon = "⚠" if agent.status.value == "degraded" else "●"
            st.markdown(
                f'<div class="agent-card">'
                f'<div class="agent-card-header">{status_icon} {agent.agent_name}</div>'
                f'<div class="agent-meta"><span class="{signal_class(agent.signal.value)}">{agent.signal.value.upper()}</span>'
                f' · {agent.confidence:.0%} · {agent.latency_ms:.0f} ms</div>'
                f'<div style="font-size:0.85rem;color:#d4d4d4;line-height:1.5">{agent.reasoning}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if agent.evidence:
                with st.expander("Evidence"):
                    for e in agent.evidence:
                        st.write(f"• {e}")
            if agent.citations:
                with st.expander(f"Citations ({len(agent.citations)})"):
                    for c in agent.citations:
                        st.markdown(f'<div class="citation"><b>{c.title}</b> · {c.relevance_score:.2f}<br><i>{c.excerpt}</i></div>', unsafe_allow_html=True)

    ch1, ch2 = st.columns(2)
    with ch1:
        fig_conf = make_confidence_bars(agents)
        if fig_conf:
            st.plotly_chart(fig_conf, use_container_width=True)
    with ch2:
        fig_lat = make_latency_bars(metrics)
        if fig_lat:
            st.plotly_chart(fig_lat, use_container_width=True)

    st.markdown("---")
    st.markdown("### Synthesized Intelligence")
    st.markdown(f"**Personalized for:** {insight.personalized_for}")
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

    with st.expander("Full Reasoning Chain"):
        st.markdown(insight.detailed_reasoning)

    if insight.citations:
        with st.expander("Source Attributions"):
            for c in insight.citations:
                st.markdown(f'<div class="citation"><b>{c.title}</b> · {c.page_or_section or "—"} · {c.relevance_score:.2f}<br>{c.excerpt}</div>', unsafe_allow_html=True)

    st.markdown("---")
    p1, p2 = st.columns([1, 1.2])
    with p1:
        st.markdown("### Portfolio")
        fig_pie = make_portfolio_pie(user)
        if fig_pie:
            st.plotly_chart(fig_pie, use_container_width=True)
        for p in user.portfolio:
            val = p.quantity * (p.current_price or p.avg_cost)
            st.write(f"• **{p.symbol.replace('.NS','')}** · {p.quantity} sh · ₹{val:,.0f} · {p.sector}")
        st.caption("Watchlist: " + (", ".join(s.replace(".NS","") for s in user.watchlist) if user.watchlist else "—"))
    with p2:
        st.markdown("### Session Metrics")
        for name, lat in metrics.agent_latencies.items():
            st.write(f"• {name}: **{lat:.0f} ms**")
        st.metric("Signal accuracy proxy", f"{metrics.signal_accuracy_proxy:.1%}" if metrics.signal_accuracy_proxy else "N/A")
        if metrics.degraded_agents:
            st.error("Degraded: " + ", ".join(metrics.degraded_agents))
        else:
            st.success("All agents healthy")
        st.caption(f"Session `{metrics.session_id}` · data source: **{data_source}**")

    st.markdown('<div class="footer">VibeFinance · PS 04 · Multi-Agent Financial Intelligence · Transparent · Personalized · Source-attributed</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()