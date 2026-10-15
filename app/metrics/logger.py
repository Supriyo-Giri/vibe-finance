"""
Session metrics capture & simple evaluation
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.agents.schemas import SessionMetrics, AgentOutput, SynthesizedInsight
from app.config import METRICS_DIR
import uuid


class MetricsLogger:
    def __init__(self):
        self.session_id = str(uuid.uuid4())[:8]
        METRICS_DIR.mkdir(parents=True, exist_ok=True)
        self.log_file = METRICS_DIR / "sessions.jsonl"

    def log_session(
        self,
        user_id: str,
        symbol: str,
        agent_outputs: List[AgentOutput],
        insight: Optional[SynthesizedInsight],
        total_latency_ms: float,
    ) -> SessionMetrics:
        latencies = {o.agent_name: round(o.latency_ms, 1) for o in agent_outputs}
        degraded = [o.agent_name for o in agent_outputs if o.status.value == "degraded"]

        # Safe handling when insight is missing
        conf = 0.5
        risk_score = 0.0
        num_cites = 0
        if insight is not None:
            conf = insight.confidence
            risk_score = insight.risk_concentration_score or 0.0
            num_cites = len(insight.citations)

        # Simple signal accuracy proxy (simulated)
        accuracy_proxy = round(
            0.45 + conf * 0.4 + (0.05 if not degraded else -0.1), 3
        )

        metrics = SessionMetrics(
            session_id=self.session_id,
            user_id=user_id,
            symbol=symbol,
            agent_latencies=latencies,
            total_latency_ms=round(total_latency_ms, 1),
            risk_concentration_score=risk_score,
            signal_accuracy_proxy=accuracy_proxy,
            num_citations=num_cites,
            degraded_agents=degraded,
        )

        # Persist
        with open(self.log_file, "a") as f:
            f.write(metrics.model_dump_json() + "\n")

        return metrics

    def get_recent(self, n: int = 10) -> List[Dict[str, Any]]:
        if not self.log_file.exists():
            return []
        lines = self.log_file.read_text().strip().split("\n")
        recent = lines[-n:]
        return [json.loads(l) for l in recent if l.strip()]