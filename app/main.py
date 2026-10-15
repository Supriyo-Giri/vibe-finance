"""
VibeFinance – Real-data Multi-Agent Financial Intelligence Dashboard
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
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background: linear-gradient(160deg, #0b0f19 0%, #111827 50%, #0f172a 100%); }
    .block-container { padding-top: 1.2rem; }
    h1, h2, h3, h4 { color: #e2e8f0 !important; }
    .console-box {
        background: #020617; border: 1px solid #1e293b; border-radius: 10px;
        padding: 14px 16px; font-family: 'JetBrains Mono', Consolas, monospace;
        font-size: 0.82rem; color: #94a3b8; max-height: 280px; overflow-y: auto; line-height: 1.55;
    }
    .console-ok { color: #4ade80; }
    .console-warn { color: #fbbf24; }
    .console-err { color: #f87171; }
    .console-info { color: #38bdf8; }
    .console-dim { color: #64748b; }
    .signal-bullish { color: #4ade80; font-weight: 800; }
    .signal-bearish { color: #f87171; font-weight: 800; }
    .signal-neutral { color: #fbbf24; font-weight: 800; }
    .signal-mixed { color: #a78bfa; font-weight: 800; }
    .kpi {
        background: #0f172a; border: 1px solid #1e293b; border-radius: 12px;
        padding: 14px 16px; text-align: center;
    }
    .kpi-label { color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; }
    .kpi-value { color: #f1f5f9; font-size: 1.35rem; font-weight: 700; margin-top: 4px; }
    .citation {
        font-size: 0.82rem; background: #020617; border-left: 3px solid #38bdf8;
        padding: 10px 12px; border-radius: 0 8px 8px 0; margin: 6px 0; color: #cbd5e1;
    }
    div[data-testid="stMetricValue"] { color: #f1f5f9 !important; }
    div[data-testid="stMetricLabel"] { color: #94a3b8 !important; }
</style>
""", unsafe_allow_html=True)


def signal_class(sig: str) -> str:
    return {
        "bullish": "signal-bullish",
        "bearish": "signal-bearish",
        "neutral": "signal-neutral",
        "mixed": "signal-mixed",
    }.get(sig.lower(), "signal-neutral")


def signal_emoji(sig: str) -> str:
    return {"bullish": "🟢", "bearish": "🔴", "neutral": "🟡", "mixed": "🟣"}.get(sig.lower(), "⚪")


@st.cache_resource
def get_pipeline():
    return VibeFinancePipeline()


def make_price_chart(symbol: str, history: list, dates: list):
    if not HAS_PLOTLY or not history:
        return None
    if not dates or len(dates) != len(history):
        dates = [str(i) for i in range(len(history))]
    color = "#4ade80" if history[-1] >= history[0] else "#f87171"
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=history, mode="lines",
        line=dict(color=color, width=2.5),
        fill="tozeroy",
        fillcolor="rgba(74,222,128,0.10)" if color == "#4ade80" else "rgba(248,113,113,0.10)",
        name=symbol,
    ))
    fig.update_layout(
        height=260, margin=dict(l=10, r=10, t=35, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", size=11),
        title=dict(text=f"{symbol} · Price history", font=dict(size=13, color="#e2e8f0")),
        xaxis=dict(showgrid=False, zeroline=False, nticks=8),
        yaxis=dict(showgrid=True, gridcolor="#1e293b", zeroline=False, tickprefix="₹"),
        showlegend=False,
    )
    return fig


def make_confidence_bars(agents):
    if not HAS_PLOTLY:
        return None
    names = [a.agent_name.replace("Agent", "") for a in agents]
    confs = [a.confidence * 100 for a in agents]
    colors = []
    for a in agents:
        colors.append(
            {"bullish": "#4ade80", "bearish": "#f87171", "mixed": "#a78bfa"}.get(
                a.signal.value, "#fbbf24"
            )
        )
    fig = go.Figure(go.Bar(
        x=confs, y=names, orientation="h",
        marker=dict(color=colors),
        text=[f"{c:.0f}%" for c in confs],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="#0f172a", size=12),
    ))
    fig.update_layout(
        height=180, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", size=11),
        title=dict(text="Agent Confidence", font=dict(size=13, color="#e2e8f0")),
        xaxis=dict(range=[0, 100], showgrid=True, gridcolor="#1e293b", ticksuffix="%"),
        yaxis=dict(showgrid=False),
    )
    return fig


def make_latency_bars(metrics):
    if not HAS_PLOTLY or not metrics.agent_latencies:
        return None
    names = list(metrics.agent_latencies.keys())
    vals = list(metrics.agent_latencies.values())
    fig = go.Figure(go.Bar(
        x=names, y=vals, marker=dict(color="#38bdf8"),
        text=[f"{v:.0f} ms" for v in vals],
        textposition="outside",
        textfont=dict(color="#94a3b8", size=11),
    ))
    fig.update_layout(
        height=200, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", size=11),
        title=dict(text="Agent Latency (ms)", font=dict(size=13, color="#e2e8f0")),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#1e293b"),
        showlegend=False,
    )
    return fig


def make_portfolio_pie(user):
    if not HAS_PLOTLY or not user.portfolio:
        return None
    labels = [p.symbol.replace(".NS", "") for p in user.portfolio]
    values = [p.quantity * (p.current_price or p.avg_cost) for p in user.portfolio]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(colors=["#38bdf8", "#4ade80", "#a78bfa", "#fbbf24", "#f87171"]),
        textinfo="label+percent",
        textfont=dict(size=11, color="#e2e8f0"),
    ))
    fig.update_layout(
        height=230, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", size=11),
        title=dict(text="Portfolio Allocation", font=dict(size=13, color="#e2e8f0")),
        showlegend=False,
    )
    return fig


def make_gauge(confidence: float, signal: str):
    if not HAS_PLOTLY:
        return None
    color = {"bullish": "#4ade80", "bearish": "#f87171", "mixed": "#a78bfa"}.get(signal, "#fbbf24")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=confidence * 100,
        number=dict(suffix="%", font=dict(size=28, color="#e2e8f0")),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor="#334155"),
            bar=dict(color=color),
            bgcolor="#0f172a",
            borderwidth=0,
            steps=[
                dict(range=[0, 40], color="#1e293b"),
                dict(range=[40, 70], color="#334155"),
                dict(range=[70, 100], color="#475569"),
            ],
        ),
        title=dict(text="Consensus Confidence", font=dict(size=13, color="#94a3b8")),
    ))
    fig.update_layout(
        height=200, margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def log_line(kind: str, msg: str) -> str:
    ts = datetime.now().strftime("%H:%M:%S")
    cls = {
        "ok": "console-ok",
        "warn": "console-warn",
        "err": "console-err",
        "info": "console-info",
    }.get(kind, "console-dim")
    return f'<span class="console-dim">[{ts}]</span> <span class="{cls}">{msg}</span>'


def main():
    st.markdown("## VibeFinance")
    st.caption("Real market data · Multi-agent analytics · RAG · Personalization")

    pipeline = get_pipeline()
    profiles = get_demo_profiles()

    with st.sidebar:
        st.markdown("### Control Panel")
        profile_key = st.selectbox(
            "Investor Profile",
            options=list(profiles.keys()),
            format_func=lambda k: f"{profiles[k].name}  ·  {k}",
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
        run_btn = st.button(" RUN MULTI-AGENT ANALYSIS", type="primary", use_container_width=True)

        st.markdown("---")
        st.markdown(f"**{user.name}**")
        st.markdown(f"Risk · `{user.risk_tolerance}`  ·  Horizon · `{user.investment_horizon}`")
        st.markdown(f"Max position · `{user.max_position_pct:.0%}`")
        for n in user.behavioral_notes:
            st.caption(f"• {n}")

        st.markdown("---")
        st.caption(f"LLM mode: `{'mock' if settings.use_mock_llm else settings.llm_model}`")
        st.caption("Data: yfinance NSE · RAG: synthetic filings")

    if not run_btn:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                '<div class="kpi"><div class="kpi-label">Agents</div>'
                '<div class="kpi-value">3 Parallel</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                '<div class="kpi"><div class="kpi-label">Data</div>'
                '<div class="kpi-value">Live yfinance</div></div>',
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                '<div class="kpi"><div class="kpi-label">Analytics</div>'
                '<div class="kpi-value">RSI · Momentum · Vol</div></div>',
                unsafe_allow_html=True,
            )
        st.info("Select profile & symbol, enable **Live market data**, then hit RUN.")
        st.markdown("""
        **Pipeline**
        1. Fetch real OHLCV from Yahoo Finance (NSE `.NS` symbols)  
        2. Compute RSI(14), 5-day momentum, volume ratio  
        3. Sentiment from real headlines (keyword model)  
        4. RAG over synthetic SEBI / earnings corpus  
        5. Personalized synthesis by risk profile  
        """)
        return

    # ── Live console ─────────────────────────────────────────
    st.markdown("###  Agent Console")
    console_placeholder = st.empty()
    logs = []

    def refresh_console():
        console_placeholder.markdown(
            '<div class="console-box">' + "<br>".join(logs) + "</div>",
            unsafe_allow_html=True,
        )

    logs.append(log_line("info", f"Session · user={user.name} · symbol={symbol} · live={use_live}"))
    logs.append(log_line("info", "Fetching market data..."))
    refresh_console()
    time.sleep(0.3)

    if force_mkt_fail:
        logs.append(log_line("warn", "Price feed forced OFF – MomentumAgent will degrade"))
    else:
        logs.append(
            log_line(
                "ok",
                "Requesting yfinance OHLCV + indicators..."
                if use_live
                else "Using cached/simulated snapshot",
            )
        )
    if force_rag_fail:
        logs.append(log_line("warn", "Filings disabled – FundamentalAgent will degrade"))
    else:
        logs.append(log_line("ok", "RAG corpus ready"))
    refresh_console()
    time.sleep(0.25)

    logs.append(log_line("info", "Dispatching MomentumAgent · SentimentAgent · FundamentalAgent"))
    refresh_console()
    for name in ["MomentumAgent", "SentimentAgent", "FundamentalAgent"]:
        logs.append(log_line("info", f"→ {name} started"))
        refresh_console()
        time.sleep(0.2)

    with st.spinner("Agents running on live data..."):
        result = asyncio.run(
            pipeline.run(
                symbol=symbol,
                user=user,
                force_rag_failure=force_rag_fail,
                force_market_failure=force_mkt_fail,
                # use_live=use_live and not force_mkt_fail,
            )
        )

    insight = result["insight"]
    agents = result["agent_outputs"]
    metrics = result["metrics"]
    mkt = result["market_data"]
    data_source = result.get("data_source", "unknown")

    for a in agents:
        if a.status.value == "degraded":
            logs.append(
                log_line(
                    "warn",
                    f"✓ {a.agent_name} DEGRADED · {a.signal.value.upper()} "
                    f"({a.confidence:.0%}) · {a.latency_ms:.0f}ms",
                )
            )
        else:
            logs.append(
                log_line(
                    "ok",
                    f"✓ {a.agent_name} · {a.signal.value.upper()} "
                    f"({a.confidence:.0%}) · {a.latency_ms:.0f}ms",
                )
            )
        refresh_console()
        time.sleep(0.12)

    logs.append(log_line("info", "SynthesisAgent · personalizing for risk profile..."))
    refresh_console()
    time.sleep(0.25)
    logs.append(
        log_line(
            "ok",
            f"Consensus {insight.overall_signal.value.upper()} · conf {insight.confidence:.0%} · "
            f"{result['total_latency_ms']:.0f}ms · data={data_source}",
        )
    )
    logs.append(log_line("ok", "Pipeline complete"))
    refresh_console()

    st.markdown("---")

    # ── KPIs ─────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(
            f'<div class="kpi"><div class="kpi-label">Signal</div>'
            f'<div class="kpi-value"><span class="{signal_class(insight.overall_signal.value)}">'
            f'{signal_emoji(insight.overall_signal.value)} {insight.overall_signal.value.upper()}'
            f"</span></div></div>",
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f'<div class="kpi"><div class="kpi-label">Confidence</div>'
            f'<div class="kpi-value">{insight.confidence:.0%}</div></div>',
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f'<div class="kpi"><div class="kpi-label">Latency</div>'
            f'<div class="kpi-value">{result["total_latency_ms"]:.0f} ms</div></div>',
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f'<div class="kpi"><div class="kpi-label">Risk HHI</div>'
            f'<div class="kpi-value">{insight.risk_concentration_score or 0:.3f}</div></div>',
            unsafe_allow_html=True,
        )
    with k5:
        st.markdown(
            f'<div class="kpi"><div class="kpi-label">Data Source</div>'
            f'<div class="kpi-value">{data_source}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("")

    # ── Charts (history comes from pipeline result – no extra import) ──
    left, right = st.columns([1.45, 1])
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
            st.warning("Price feed unavailable")
    with right:
        fig_gauge = make_gauge(insight.confidence, insight.overall_signal.value)
        if fig_gauge:
            st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("---")

    # ── Agent cards ──────────────────────────────────────────
    st.markdown("###  Agent Results")
    cols = st.columns(len(agents))
    for col, agent in zip(cols, agents):
        with col:
            icon = "⚠️" if agent.status.value == "degraded" else "✅"
            st.markdown(f"**{icon} {agent.agent_name}**")
            st.markdown(
                f"<span class='{signal_class(agent.signal.value)}'>{agent.signal.value.upper()}</span>"
                f" · {agent.confidence:.0%} · {agent.latency_ms:.0f} ms",
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
                            f"<div class='citation'><b>{c.title}</b> · {c.relevance_score:.2f}<br>"
                            f"<i>{c.excerpt}</i></div>",
                            unsafe_allow_html=True,
                        )

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

    # ── Synthesis ────────────────────────────────────────────
    st.markdown("### Synthesized Intelligence")
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

    with st.expander(" Full Reasoning Chain"):
        st.markdown(insight.detailed_reasoning)

    if insight.citations:
        with st.expander(" Source Attributions"):
            for c in insight.citations:
                st.markdown(
                    f"<div class='citation'><b>{c.title}</b> · {c.page_or_section} · "
                    f"{c.relevance_score:.2f}<br>{c.excerpt}</div>",
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # ── Portfolio + metrics ──────────────────────────────────
    p1, p2 = st.columns([1, 1.2])
    with p1:
        st.markdown("### Portfolio")
        fig_pie = make_portfolio_pie(user)
        if fig_pie:
            st.plotly_chart(fig_pie, use_container_width=True)
        for p in user.portfolio:
            val = p.quantity * (p.current_price or p.avg_cost)
            st.write(f"• **{p.symbol}** · {p.quantity} sh · ₹{val:,.0f} · {p.sector}")
        st.markdown("**Watchlist:** " + (", ".join(user.watchlist) if user.watchlist else "—"))
    with p2:
        st.markdown("### Session Metrics")
        for name, lat in metrics.agent_latencies.items():
            st.write(f"• {name}: **{lat:.0f} ms**")
        st.metric(
            "Signal accuracy proxy",
            f"{metrics.signal_accuracy_proxy:.1%}" if metrics.signal_accuracy_proxy else "N/A",
        )
        if metrics.degraded_agents:
            st.error("Degraded: " + ", ".join(metrics.degraded_agents))
        else:
            st.success("All agents healthy")
        st.caption(f"Session `{metrics.session_id}` · data source: **{data_source}**")


if __name__ == "__main__":
    main()