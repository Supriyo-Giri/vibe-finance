"""
Quick smoke test – run without Streamlit
python -m tests.smoke_test
"""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.pipeline import VibeFinancePipeline
from app.user.profiles import get_demo_profiles


async def main():
    pipe = VibeFinancePipeline()
    profiles = get_demo_profiles()

    print("=" * 60)
    print("VibeFinance Smoke Test")
    print("=" * 60)

    for profile_key in ["conservative", "aggressive"]:
        user = profiles[profile_key]
        print(f"\n>>> Profile: {user.name} ({user.risk_tolerance})")
        result = await pipe.run(symbol="INFY.NS", user=user)
        insight = result["insight"]
        print(f"  Overall: {insight.overall_signal.value} | conf={insight.confidence:.0%}")
        print(f"  Summary: {insight.summary}")
        print(f"  Recommendations:")
        for r in insight.recommendations:
            print(f"    • {r}")
        print(f"  Latency: {result['total_latency_ms']:.0f} ms | Citations: {len(insight.citations)}")

    # Degraded path
    print("\n>>> Degraded RAG test")
    user = profiles["moderate"]
    result = await pipe.run(symbol="TCS.NS", user=user, force_rag_failure=True)
    degraded = [a.agent_name for a in result["agent_outputs"] if a.status.value == "degraded"]
    print(f"  Degraded agents: {degraded}")
    print(f"  Still produced insight: {result['insight'].overall_signal.value}")

    print("\n✅ Smoke test passed")


if __name__ == "__main__":
    asyncio.run(main())