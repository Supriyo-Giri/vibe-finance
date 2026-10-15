"""
Pre-defined user profiles for personalization demo
"""
from app.agents.schemas import UserProfile, PortfolioPosition


def get_demo_profiles() -> dict[str, UserProfile]:
    return {
        "conservative": UserProfile(
            user_id="user_cons_01",
            name="Priya Sharma",
            risk_tolerance="conservative",
            investment_horizon="long",
            max_position_pct=0.08,
            preferred_sectors=["Banking", "FMCG", "IT"],
            avoided_sectors=["Crypto", "High-beta smallcap"],
            behavioral_notes=[
                "Prefers capital protection over high returns",
                "Has previously sold winners too early",
                "Checks portfolio weekly",
            ],
            portfolio=[
                PortfolioPosition(symbol="HDFCBANK.NS", quantity=50, avg_cost=1450, current_price=1680, sector="Banking"),
                PortfolioPosition(symbol="TCS.NS", quantity=20, avg_cost=3200, current_price=3850, sector="IT"),
                PortfolioPosition(symbol="RELIANCE.NS", quantity=15, avg_cost=2400, current_price=2950, sector="Energy"),
            ],
            watchlist=["INFY.NS", "ICICIBANK.NS"],
        ),
        "aggressive": UserProfile(
            user_id="user_agg_01",
            name="Arjun Mehta",
            risk_tolerance="aggressive",
            investment_horizon="medium",
            max_position_pct=0.20,
            preferred_sectors=["IT", "Consumer Discretionary", "New Energy"],
            avoided_sectors=[],
            behavioral_notes=[
                "Comfortable with higher volatility",
                "Often adds on dips",
                "Follows technical breakouts",
            ],
            portfolio=[
                PortfolioPosition(symbol="TCS.NS", quantity=40, avg_cost=3100, current_price=3850, sector="IT"),
                PortfolioPosition(symbol="INFY.NS", quantity=60, avg_cost=1400, current_price=1780, sector="IT"),
                PortfolioPosition(symbol="RELIANCE.NS", quantity=25, avg_cost=2500, current_price=2950, sector="Energy"),
            ],
            watchlist=["HDFCBANK.NS", "ICICIBANK.NS"],
        ),
        "moderate": UserProfile(
            user_id="user_mod_01",
            name="Neha Kapoor",
            risk_tolerance="moderate",
            investment_horizon="medium",
            max_position_pct=0.12,
            preferred_sectors=["Banking", "IT", "Pharma"],
            avoided_sectors=["Highly leveraged"],
            behavioral_notes=["Rebalances quarterly", "Avoids FOMO entries"],
            portfolio=[
                PortfolioPosition(symbol="ICICIBANK.NS", quantity=80, avg_cost=900, current_price=1120, sector="Banking"),
                PortfolioPosition(symbol="TCS.NS", quantity=15, avg_cost=3400, current_price=3850, sector="IT"),
            ],
            watchlist=["RELIANCE.NS", "HDFCBANK.NS", "INFY.NS"],
        ),
    }