# VibeFinance Architecture

**PS 04 – Multi-Agent Autonomous Financial Intelligence for Retail Investors**

This document describes the system architecture, agent roles, decision logic, data flow, failure handling, and evaluation approach of the VibeFinance MVP.

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Streamlit Dashboard                          │
│  (Control Panel · Live Console · Signals · Citations · Metrics)    │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     VibeFinancePipeline                             │
│  Orchestrator: data ingestion → parallel agents → synthesis → log   │
└───────┬───────────────────────┬───────────────────────┬─────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐     ┌─────────────────┐     ┌────────────────────┐
│ MomentumAgent │     │ SentimentAgent  │     │ FundamentalAgent   │
│ (Price/RSI/   │     │ (Headlines +    │     │ (RAG over filings  │
│  Momentum)    │     │  Keyword model) │     │  & transcripts)    │
└───────┬───────┘     └────────┬────────┘     └─────────┬──────────┘
        │                      │                        │
        └──────────────────────┼────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   SynthesisAgent    │
                    │ (Conflict resolution│
                    │  + Personalization) │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   MetricsLogger     │
                    │ (Latency · Risk ·   │
                    │  Citations · Acc.)  │
                    └─────────────────────┘
```

**Core principle**: Every recommendation is produced by specialized agents running in parallel, grounded in either market data or retrieved documents, and then synthesized under the constraints of an individual investor profile. No uncited or opaque recommendation is emitted.

---

## 2. Component Overview

| Component | Responsibility | Key Files |
|-----------|----------------|-----------|
| **Dashboard** | Interactive UI, profile selection, failure injection, visualization of signals / citations / metrics | `app/main.py` |
| **Pipeline** | End-to-end orchestration, parallel dispatch, synthesis fallback | `app/pipeline.py` |
| **MomentumAgent** | Price momentum, RSI(14), short-term technical classification | `app/agents/momentum_agent.py` |
| **SentimentAgent** | Headline / news sentiment scoring | `app/agents/sentiment_agent.py` |
| **FundamentalAgent** | Retrieval-augmented analysis of filings & earnings documents | `app/agents/fundamental_agent.py` |
| **SynthesisAgent** | Weighted consensus, conflict resolution, personalization | `app/agents/synthesis_agent.py` |
| **DocumentRetriever** | Semantic search over synthetic SEBI / earnings corpus | `app/rag/retriever.py` |
| **Market Data Layer** | Live yfinance OHLCV + indicators (with simulated fallback) | `app/data/market_data.py` |
| **User Profiles** | Risk tolerance, horizon, portfolio, behavioral notes | `app/user/profiles.py` |
| **MetricsLogger** | Session latency, risk concentration, citation count, degraded agents | `app/metrics/logger.py` |
| **Schemas** | Strict output contracts for all agents and insights | `app/agents/schemas.py` |

---

## 3. Agent Roles & Structured Output Contracts

All agents inherit a common base and return a uniform `AgentOutput` (Pydantic model):

```python
class AgentOutput(BaseModel):
    agent_name: str
    dimension: str                  # e.g. "price_momentum", "sentiment", "fundamental"
    signal: SignalLabel             # bullish | bearish | neutral | mixed
    confidence: float               # 0.0 – 1.0
    reasoning: str                  # human-readable explanation
    evidence: List[str]
    citations: List[Citation]       # only FundamentalAgent populates this in MVP
    status: AgentStatus             # success | degraded | failed
    latency_ms: float
    metadata: Dict[str, Any]
```

### 3.1 MomentumAgent
- **Dimension**: Price momentum & technicals
- **Inputs**: OHLCV history, RSI(14), 5-day / 20-day returns, volume ratio
- **Logic**: Rule-based thresholds on RSI and momentum + volume confirmation
- **Output**: Signal + confidence + evidence list (e.g. “RSI = 68.2, 5d momentum = +4.1%”)

### 3.2 SentimentAgent
- **Dimension**: Market / news sentiment
- **Inputs**: Recent headlines (or simulated headline set)
- **Logic**: Keyword polarity model with intensity weighting
- **Output**: Signal + confidence + supporting headline snippets

### 3.3 FundamentalAgent (RAG-grounded)
- **Dimension**: Fundamental / regulatory
- **Inputs**: Symbol + company name → DocumentRetriever
- **Logic**:
  1. Semantic retrieval (top-k documents above similarity threshold)
  2. Grounded reasoning over retrieved excerpts
  3. Citation objects attached to the output
- **Graceful degradation**: If no documents retrieved or force-failure flag is set → status = `degraded`, lower confidence, explicit warning in reasoning

### 3.4 SynthesisAgent
- **Role**: Single source of truth for the final recommendation
- **Inputs**: List of `AgentOutput` + `UserProfile` + market snapshot
- **Decision logic** (see Section 5)

---

## 4. Data Flow (End-to-End)

1. **User selects** investor profile + symbol + optional failure flags in the dashboard.
2. **Pipeline.run()** is invoked.
3. **Market data** is fetched via yfinance (or simulated if live feed is unavailable / forced off).
4. **Sentiment snapshot** is generated from headlines.
5. **Three agents** are launched concurrently via `asyncio.gather(..., return_exceptions=True)`.
6. Each agent produces a structured `AgentOutput` (or raises → treated as degraded).
7. **SynthesisAgent** consumes the agent outputs + user profile and produces a `SynthesizedInsight`.
8. **MetricsLogger** records latencies, risk concentration score, citation count, and degraded agents.
9. Dashboard renders:
   - Overall signal + confidence gauge
   - Per-agent signals & reasoning
   - Visible citations with relevance scores
   - Portfolio impact statement tailored to the user
   - Session metrics

The full reasoning chain (agent outputs → synthesis summary → personalized recommendations) is visible in the UI.

---

## 5. Synthesis & Decision Logic

The SynthesisAgent implements a transparent, deterministic consensus process:

1. **Collect valid outputs** (ignore pure failures; keep degraded agents with reduced weight).
2. **Signal aggregation**:
   - Map signals to numeric scores: bullish = +1, neutral = 0, bearish = –1, mixed = 0.
   - Weight each agent by its reported confidence (and by a dimension importance factor if desired).
   - Compute weighted average → overall signal + consensus confidence.
3. **Conflict detection**:
   - If agents disagree significantly (e.g., one strong bullish + one strong bearish), overall signal becomes `mixed` and confidence is reduced.
   - Disagreement is explicitly called out in the `detailed_reasoning` field.
4. **Personalization**:
   - Risk tolerance modulates position-sizing language and risk warnings.
   - Existing portfolio concentration is calculated → `risk_concentration_score`.
   - Behavioral notes influence the tone of recommendations (e.g., “avoid FOMO entries”).
   - Max position % and preferred/avoided sectors constrain suggestions.
5. **Output**: `SynthesizedInsight` containing:
   - Overall signal & confidence
   - Executive summary
   - Detailed reasoning (includes agent contributions)
   - Actionable recommendations
   - Risk warnings
   - Full list of agent outputs + citations
   - Portfolio impact statement

No recommendation is emitted without an accompanying reasoning chain and source attribution where applicable.

---

## 6. Retrieval-Augmented Generation (RAG)

- **Corpus**: Synthetic but realistic SEBI-style filings, board meeting outcomes, and earnings-call excerpts stored under `data/filings`.
- **Retriever**: Sentence-transformer embeddings + ChromaDB (or lightweight fallback) with configurable top-k and similarity threshold.
- **Grounding rule**: FundamentalAgent **must** attach at least one `Citation` object when documents are successfully retrieved. If retrieval fails, the agent degrades and states that no source material was available.
- **Visibility**: Citations (title, excerpt, relevance score) are rendered in the dashboard with clear visual distinction.

This satisfies the mandatory requirement that at least one agent output is grounded in retrieved source material with visible attribution.

---

## 7. Personalization Model

User profiles are first-class citizens:

```python
class UserProfile(BaseModel):
    user_id: str
    name: str
    risk_tolerance: Literal["conservative", "moderate", "aggressive"]
    investment_horizon: Literal["short", "medium", "long"]
    max_position_pct: float
    preferred_sectors / avoided_sectors
    behavioral_notes: List[str]
    portfolio: List[PortfolioPosition]
    watchlist: List[str]
```

**Demonstration of personalization**:  
Identical market data + agent outputs fed to a conservative vs. aggressive profile produce different recommendation language, risk warnings, and suggested position sizes. This difference is observable in the dashboard by switching profiles.

---

## 8. Graceful Failure Handling

The system is designed never to crash the pipeline or emit uncited recommendations:

| Failure Mode | Handling |
|--------------|----------|
| Price feed unavailable | MomentumAgent returns `status=degraded`, reduced confidence, explicit note |
| No relevant filings | FundamentalAgent returns `status=degraded`, empty citations, warning in reasoning |
| Agent exception | Caught by `return_exceptions=True`; treated as degraded |
| Synthesis failure | Hard fallback `SynthesizedInsight` with neutral signal + error explanation |
| Conflicting agent signals | Explicitly surfaced as `mixed` with lowered confidence and reasoning that names the conflict |

Failure injection toggles in the dashboard allow judges to trigger these paths live.

---

## 9. Performance Logging & Evaluation Metrics

Every session records (via `MetricsLogger`):

- Per-agent latency (ms)
- End-to-end latency
- Risk concentration score (derived from current portfolio weights)
- Number of citations attached
- List of degraded agents
- Optional signal-accuracy proxy (can be extended with historical forward-return evaluation)

These metrics are displayed in the dashboard and persisted under `data/metrics/`.

---

## 10. Technology Stack

| Layer | Technology |
|-------|------------|
| UI | Streamlit + Plotly |
| Orchestration | asyncio (parallel agents) |
| Data models | Pydantic v2 |
| Market data | yfinance (NSE `.NS` symbols) with simulated fallback |
| Embeddings / RAG | sentence-transformers + ChromaDB |
| LLM (optional) | OpenAI-compatible API or mock mode (`USE_MOCK_LLM=true`) |
| Metrics | Custom logger + JSON persistence |

---

## 11. Design Decisions & Trade-offs

- **Rule-based + retrieval over pure LLM generation** for the core signal agents → higher determinism, lower cost, easier auditing of reasoning.
- **Strict structured outputs** → synthesis can reason about confidence and status programmatically.
- **Parallelism with isolation** → one agent’s failure never blocks the others.
- **Synthetic filings** → acceptable under the problem statement when live regulatory data access is unavailable; clearly disclosed in the UI.
- **Mock LLM mode by default** → system remains fully functional without API keys.

---

## 12. Future Extension Points

- Additional specialized agents (Volume Anomaly, Options Flow, Macro Regime)
- Historical back-testing harness for true signal accuracy vs. 30-day forward returns
- Persistent user sessions and decision history
- Real-time streaming of NSE / SEBI data feeds
- Confidence calibration and inter-agent disagreement quantification

---

*This architecture prioritizes transparency, source attribution, personalization, and reliability — the four pillars required by the PS 04 judging rubric.*
