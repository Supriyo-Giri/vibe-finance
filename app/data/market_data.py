"""
Real market data via yfinance + technical indicators.
Falls back to simulated data if network/API fails.
"""
from typing import Dict, Any, Optional, List
import random

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
    HAS_YF = True
except ImportError:
    HAS_YF = False


SIMULATED_MARKET = {
    "RELIANCE.NS": {
        "last_price": 2950.40, "change_1d_pct": 1.25, "momentum_5d_pct": 3.8,
        "rsi_14": 62.4, "volume_ratio": 1.45, "sector": "Energy",
        "company_name": "Reliance Industries",
        "history": [2780, 2810, 2795, 2840, 2885, 2910, 2895, 2920, 2945, 2950.40],
        "history_dates": [],
    },
    "TCS.NS": {
        "last_price": 3850.20, "change_1d_pct": -0.45, "momentum_5d_pct": 1.2,
        "rsi_14": 54.1, "volume_ratio": 0.92, "sector": "IT",
        "company_name": "Tata Consultancy Services",
        "history": [3720, 3755, 3780, 3800, 3825, 3840, 3865, 3870, 3860, 3850.20],
        "history_dates": [],
    },
    "INFY.NS": {
        "last_price": 1780.50, "change_1d_pct": 0.85, "momentum_5d_pct": 4.6,
        "rsi_14": 68.7, "volume_ratio": 1.85, "sector": "IT",
        "company_name": "Infosys",
        "history": [1650, 1675, 1690, 1710, 1725, 1740, 1755, 1768, 1772, 1780.50],
        "history_dates": [],
    },
    "HDFCBANK.NS": {
        "last_price": 1680.00, "change_1d_pct": -1.10, "momentum_5d_pct": -2.3,
        "rsi_14": 41.2, "volume_ratio": 1.60, "sector": "Banking",
        "company_name": "HDFC Bank",
        "history": [1750, 1735, 1720, 1710, 1705, 1695, 1690, 1700, 1695, 1680.00],
        "history_dates": [],
    },
    "ICICIBANK.NS": {
        "last_price": 1120.75, "change_1d_pct": 0.35, "momentum_5d_pct": 2.1,
        "rsi_14": 57.8, "volume_ratio": 1.15, "sector": "Banking",
        "company_name": "ICICI Bank",
        "history": [1080, 1090, 1095, 1105, 1110, 1115, 1118, 1122, 1119, 1120.75],
        "history_dates": [],
    },
}

SIMULATED_SENTIMENT = {
    "RELIANCE.NS": {"positive": 0.48, "negative": 0.22, "neutral": 0.30,
                    "sample_headlines": ["Reliance Retail expands footprint", "Jio subscriber growth continues"]},
    "TCS.NS": {"positive": 0.55, "negative": 0.18, "neutral": 0.27,
               "sample_headlines": ["TCS wins multi-year deal", "Strong deal pipeline"]},
    "INFY.NS": {"positive": 0.42, "negative": 0.28, "neutral": 0.30,
                "sample_headlines": ["Infosys cautious guidance", "GenAI deals gaining traction"]},
    "HDFCBANK.NS": {"positive": 0.35, "negative": 0.32, "neutral": 0.33,
                    "sample_headlines": ["HDFC Bank NIMs under pressure", "Deposit growth improves"]},
    "ICICIBANK.NS": {"positive": 0.52, "negative": 0.20, "neutral": 0.28,
                     "sample_headlines": ["ICICI market share gains", "Asset quality stable"]},
}

SECTOR_MAP = {
    "RELIANCE.NS": "Energy", "TCS.NS": "IT", "INFY.NS": "IT",
    "HDFCBANK.NS": "Banking", "ICICIBANK.NS": "Banking",
}


def _rsi(series, period: int = 14) -> float:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    val = rsi.iloc[-1]
    return float(val) if not np.isnan(val) else 50.0


def _fetch_one(symbol: str, period: str = "3mo") -> Optional[Dict[str, Any]]:
    if not HAS_YF:
        return None
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period=period, auto_adjust=True)
        if hist is None or hist.empty or len(hist) < 20:
            return None

        close = hist["Close"]
        volume = hist["Volume"]
        last = float(close.iloc[-1])
        prev = float(close.iloc[-2]) if len(close) > 1 else last
        change_1d = ((last - prev) / prev) * 100 if prev else 0.0

        if len(close) >= 6:
            mom = ((last - float(close.iloc[-6])) / float(close.iloc[-6])) * 100
        else:
            mom = change_1d

        rsi_val = _rsi(close, 14)

        vol_avg = float(volume.tail(20).mean()) if len(volume) >= 20 else float(volume.mean())
        vol_last = float(volume.iloc[-1])
        vol_ratio = vol_last / vol_avg if vol_avg > 0 else 1.0

        hist_slice = hist.tail(30)
        history = [round(float(x), 2) for x in hist_slice["Close"].tolist()]
        history_dates = [d.strftime("%d %b") for d in hist_slice.index]

        info = {}
        try:
            info = t.info or {}
        except Exception:
            info = {}
        name = info.get("shortName") or info.get("longName") or symbol.replace(".NS", "")
        sector = info.get("sector") or SECTOR_MAP.get(symbol, "Unknown")

        headlines = []
        try:
            news = t.news or []
            for n in news[:4]:
                title = n.get("title") or (n.get("content") or {}).get("title")
                if title:
                    headlines.append(title[:120])
        except Exception:
            pass

        return {
            "last_price": round(last, 2),
            "change_1d_pct": round(change_1d, 2),
            "momentum_5d_pct": round(mom, 2),
            "rsi_14": round(rsi_val, 1),
            "volume_ratio": round(vol_ratio, 2),
            "sector": sector,
            "company_name": name,
            "history": history,
            "history_dates": history_dates,
            "headlines": headlines,
            "source": "yfinance",
        }
    except Exception as e:
        print(f"[market_data] yfinance failed for {symbol}: {e}")
        return None


def _sentiment_from_headlines(headlines: List[str]) -> Dict[str, Any]:
    if not headlines:
        return {"positive": 0.34, "negative": 0.33, "neutral": 0.33, "sample_headlines": ["No recent headlines"]}

    pos_kw = ["growth", "profit", "surge", "gain", "beat", "strong", "record", "win", "rise", "up", "boost", "expand"]
    neg_kw = ["fall", "drop", "loss", "miss", "weak", "cut", "risk", "decline", "pressure", "slow", "down", "slump"]

    pos = neg = 0
    for h in headlines:
        hl = h.lower()
        for k in pos_kw:
            if k in hl:
                pos += 1
        for k in neg_kw:
            if k in hl:
                neg += 1

    total = pos + neg + 1
    p = pos / total
    n = neg / total
    neu = max(0.0, 1.0 - p - n)
    s = p + n + neu
    return {
        "positive": round(p / s, 2),
        "negative": round(n / s, 2),
        "neutral": round(neu / s, 2),
        "sample_headlines": headlines[:3],
    }


def get_market_snapshot(symbols: Optional[list[str]] = None, use_live: bool = True) -> Dict[str, Any]:
    symbols = symbols or list(SIMULATED_MARKET.keys())
    data = {}
    for s in symbols:
        live = _fetch_one(s) if use_live else None
        if live:
            data[s] = live
        elif s in SIMULATED_MARKET:
            data[s] = SIMULATED_MARKET[s].copy()
            data[s]["source"] = "simulated"
        else:
            data[s] = {
                "last_price": 0, "change_1d_pct": 0, "momentum_5d_pct": 0,
                "rsi_14": 50, "volume_ratio": 1.0, "sector": "Unknown",
                "company_name": s, "history": [], "history_dates": [],
                "source": "empty",
            }
    return data


def get_sentiment_snapshot(symbols: Optional[list[str]] = None, market_data: Optional[Dict] = None) -> Dict[str, Any]:
    symbols = symbols or list(SIMULATED_SENTIMENT.keys())
    data = {}
    for s in symbols:
        headlines = []
        if market_data and s in market_data:
            headlines = market_data[s].get("headlines") or []
        if headlines:
            data[s] = _sentiment_from_headlines(headlines)
            data[s]["source"] = "headlines"
        elif s in SIMULATED_SENTIMENT:
            data[s] = SIMULATED_SENTIMENT[s].copy()
            data[s]["source"] = "simulated"
        else:
            data[s] = {"positive": 0.34, "negative": 0.33, "neutral": 0.33,
                       "sample_headlines": ["No headlines"], "source": "empty"}
    return data


def get_company_name(symbol: str) -> str:
    snap = get_market_snapshot([symbol], use_live=False)
    if symbol in snap:
        return snap[symbol].get("company_name", symbol)
    return symbol.replace(".NS", "")

def get_price_history(symbol: str) -> List[float]:
    snap = get_market_snapshot([symbol], use_live=True)
    return snap.get(symbol, {}).get("history", [])


def get_price_history_with_dates(symbol: str) -> tuple:
    snap = get_market_snapshot([symbol], use_live=True)
    d = snap.get(symbol, {})
    return d.get("history", []), d.get("history_dates", [])