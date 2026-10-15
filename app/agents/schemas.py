"""
Structured output contracts for all agents
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from enum import Enum


class SignalLabel(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class AgentStatus(str, Enum):
    SUCCESS = "success"
    DEGRADED = "degraded"
    FAILED = "failed"


class Citation(BaseModel):
    source_id: str
    title: str
    excerpt: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    page_or_section: Optional[str] = None


class AgentOutput(BaseModel):
    agent_name: str
    dimension: str
    signal: SignalLabel
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    evidence: List[str] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    status: AgentStatus = AgentStatus.SUCCESS
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PortfolioPosition(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float
    current_price: Optional[float] = None
    sector: Optional[str] = None


class UserProfile(BaseModel):
    user_id: str
    name: str
    risk_tolerance: Literal["conservative", "moderate", "aggressive"]
    investment_horizon: Literal["short", "medium", "long"]
    max_position_pct: float = 0.15
    preferred_sectors: List[str] = Field(default_factory=list)
    avoided_sectors: List[str] = Field(default_factory=list)
    behavioral_notes: List[str] = Field(default_factory=list)
    portfolio: List[PortfolioPosition] = Field(default_factory=list)
    watchlist: List[str] = Field(default_factory=list)


class SynthesizedInsight(BaseModel):
    overall_signal: SignalLabel
    confidence: float
    summary: str
    detailed_reasoning: str
    recommendations: List[str]
    risk_warnings: List[str]
    agent_outputs: List[AgentOutput]
    citations: List[Citation]
    personalized_for: str
    portfolio_impact: Optional[str] = None
    risk_concentration_score: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SessionMetrics(BaseModel):
    session_id: str
    user_id: str
    symbol: str
    agent_latencies: Dict[str, float]
    total_latency_ms: float
    risk_concentration_score: float
    signal_accuracy_proxy: Optional[float] = None
    num_citations: int
    degraded_agents: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)