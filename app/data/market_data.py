"""
Market data provider – simulated realistic data for demo
Includes short price history for charts.
"""
from typing import Dict, Any, Optional, List
import random


SIMULATED_MARKET = {
    "RELIANCE.NS": {
        "last_price": 2950.40,
        "change_1d_pct": 1.25,
        "momentum_5d_pct": 3.8,
        "rsi_14": 62.4,
        "volume_ratio": 1.45,
        "sector": "Energy",
        "company_name": "Reliance Industries",
        "history": [2780, 2810, 2795, 2840, 2885, 2910, 2895, 2920, 2945, 2950.40],
    },
    "TCS.NS": {
        "last_price": 3850.20,
        "change_1d_pct": -0.45,
        "momentum_5d_pct": 1.2,
        "rsi_14": 54.1,
        "volume_ratio": 0.92,
        "sector": "IT",
        "company_name": "Tata Consultancy Services",
        "history": [3720, 3755, 3780, 3800, 3825, 3840, 3865, 3870, 3860, 3850.20],
    },
    "INFY.NS": {
        "last_price": 1780.50,
        "change_1d_pct": 0.85,
        "momentum_5d_pct": 4.6,
        "rsi_14": 68.7,
        "volume_ratio": 1.85,
        "sector": "IT",
        "company_name": "Infosys",
        "history": [1650, 1675, 1690, 1710, 1725, 1740, 1755, 1768, 1772, 1780.50],
    },
    "HDFCBANK.NS": {
        "last_price": 1680.00,
        "change_1d_pct": -1.10,
        "momentum_5d_pct": -2.3,
        "rsi_14": 41.2,
        "volume_ratio": 1.60,
        "sector": "Banking",
        "company_name": "HDFC Bank",
        "history": [1750, 1735, 1720, 1710, 1705, 1695, 1690, 1700, 1695, 1680.00],
    },
    "ICICIBANK.NS": {
        "last_price": 1120.75,
        "change_1d_pct": 0.35,
        "momentum_5d_pct": 2.1,
        "rsi_14": 57.8,
        "volume_ratio": 1.15,
        "sector": "Banking",
        "company_name": "ICICI Bank",
        "history": [1080, 1090, 1095, 1105, 1110, 1115, 1118, 1122, 1119, 1120.75],
    },
}


SIMULATED_SENTIMENT = {
    "RELIANCE.NS": {
        "positive": 0.48,
        "negative": 0.22,
        "neutral": 0.30,
        "sample_headlines": [
            "Reliance Retail expands footprint in Tier-2 cities",
            "Jio adds strong subscriber base in latest quarter",
        ],
    },
    "TCS.NS": {
        "positive": 0.55,
        "negative": 0.18,
        "neutral": 0.27,
        "sample_headlines": [
            "TCS wins multi-year deal with European bank",
            "IT major maintains strong deal pipeline",
        ],
    },
    "INFY.NS": {
        "positive": 0.42,
        "negative": 0.28,
        "neutral": 0.30,
        "sample_headlines": [
            "Infosys guidance remains cautious amid client delays",
            "GenAI deals gaining traction for Infosys",
        ],
    },
    "HDFCBANK.NS": {
        "positive": 0.35,
        "negative": 0.32,
        "neutral": 0.33,
        "sample_headlines": [
            "HDFC Bank NIMs under pressure post merger",
            "Private bank deposit growth shows sequential improvement",
        ],
    },
    "ICICIBANK.NS": {
        "positive": 0.52,
        "negative": 0.20,
        "neutral": 0.28,
        "sample_headlines": [
            "ICICI Bank continues market share gains in retail",
            "Strong quarter for ICICI; asset quality stable",
        ],
    },
}


def get_market_snapshot(symbols: Optional[list[str]] = None) -> Dict[str, Any]:
    symbols = symbols or list(SIMULATED_MARKET.keys())
    data = {}
    for s in symbols:
        if s in SIMULATED_MARKET:
            data[s] = SIMULATED_MARKET[s].copy()
        else:
            data[s] = {
                "last_price": round(random.uniform(500, 4000), 2),
                "change_1d_pct": round(random.uniform(-3, 3), 2),
                "momentum_5d_pct": round(random.uniform(-5, 6), 2),
                "rsi_14": round(random.uniform(30, 75), 1),
                "volume_ratio": round(random.uniform(0.7, 2.2), 2),
                "sector": "Unknown",
                "company_name": s,
                "history": [round(random.uniform(500, 4000), 2) for _ in range(10)],
            }
    return data


def get_sentiment_snapshot(symbols: Optional[list[str]] = None) -> Dict[str, Any]:
    symbols = symbols or list(SIMULATED_SENTIMENT.keys())
    data = {}
    for s in symbols:
        if s in SIMULATED_SENTIMENT:
            data[s] = SIMULATED_SENTIMENT[s].copy()
        else:
            data[s] = {
                "positive": 0.34,
                "negative": 0.33,
                "neutral": 0.33,
                "sample_headlines": ["No recent headlines available"],
            }
    return data


def get_company_name(symbol: str) -> str:
    return SIMULATED_MARKET.get(symbol, {}).get("company_name", symbol)


def get_price_history(symbol: str) -> List[float]:
    return SIMULATED_MARKET.get(symbol, {}).get("history", [])