import os
import os
import time
import io
import logging
from typing import List, Dict, Any, Optional, Tuple
 
import httpx
import numpy as np
import pandas as pd
 
logger = logging.getLogger(__name__)
 
# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
 
LARGE_CAP_THRESHOLD = 50000   # ₹50,000 Cr
MID_CAP_THRESHOLD   = 10000   # ₹10,000 Cr
RISK_FREE_RATE      = 0.065   # ~6.5% (India 10yr G-sec)
 
# Final score layer weights
SCORE_WEIGHTS = {
    "news_sentiment": 0.35,
    "macro_trend":    0.25,
    "fundamental":    0.25,
    "momentum":       0.15,
}
 
# ─────────────────────────────────────────────
# RISK PROFILES
# ─────────────────────────────────────────────
 
RISK_PROFILES = {
    "safe": {
        "min_market_cap":      LARGE_CAP_THRESHOLD,
        "max_volatility":      0.25,
        "min_earnings_growth": -0.1,
        "volatility_weight":   0.3,
        "returns_weight":      0.2,
    },
    "moderate": {
        "min_market_cap":      MID_CAP_THRESHOLD,
        "max_volatility":      0.40,
        "min_earnings_growth": -0.05,
        "volatility_weight":   0.2,
        "returns_weight":      0.3,
    },
    "aggressive": {
        "min_market_cap":      0,
        "max_volatility":      1.0,
        "min_earnings_growth": -1.0,
        "volatility_weight":   0.1,
        "returns_weight":      0.4,
    },
}
 
# ─────────────────────────────────────────────
# NSE INDEX UNIVERSE
# ─────────────────────────────────────────────
 
INDEX_URLS = {
    "nifty50":      "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv",
    "nifty100":     "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv",
    "nifty200":     "https://www.niftyindices.com/IndexConstituent/ind_nifty200list.csv",
    "nifty500":     "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv",
    "nifty_midcap": "https://www.niftyindices.com/IndexConstituent/ind_niftymidcap150list.csv",
    "nifty_small":  "https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap250list.csv",
}
 
RISK_TO_INDEX = {
    "safe":       "nifty50",
    "moderate":   "nifty200",
    "aggressive": "nifty500",
}
 
# Nifty sectoral indices on yfinance (for macro trend layer)
SECTOR_INDICES = {
    "FINANCIAL SERVICES": "^NSEBANK",
    "INFORMATION TECHNOLOGY": "^CNXIT",
    "PHARMA": "^CNXPHARMA",
    "AUTO": "^CNXAUTO",
    "INFRASTRUCTURE": "^CNXINFRA",
    "ENERGY": "^CNXENERGY",
    "MEDIA": "^CNXMEDIA",
    "METAL": "^CNXMETAL",
    "REALTY": "^CNXREALTY",
    "FMCG": "^CNXFMCG",
}
 
# High-conviction macro themes for India (editorial — update quarterly)
MACRO_THEMES = {
    "Defence":    ["HAL.NS", "BEL.NS", "GRSE.NS", "COCHINSHIP.NS", "PARAS.NS"],
    "EV":         ["TATAMOTORS.NS", "MOTHERSON.NS", "EXIDEIND.NS", "BOSCHLTD.NS"],
    "Infra/CapEx":["LT.NS", "IRFC.NS", "RVNL.NS", "POLYCAB.NS", "ABB.NS"],
    "AI/Data":    ["TCS.NS", "INFY.NS", "LTTS.NS", "PERSISTENT.NS", "COFORGE.NS"],
    "Pharma/CDMO":["DIVI.NS", "SUNPHARMA.NS", "LAURUS.NS", "AUROPHARMA.NS", "CIPLA.NS"],
    "Renewables": ["ADANIGREEN.NS", "NTPC.NS", "TATAPOWER.NS", "SJVN.NS"],
    "PSU Banks":  ["SBIN.NS", "PNB.NS", "CANARABANK.NS", "BANKBARODA.NS"],
    "Consumption":["TITAN.NS", "DMART.NS", "ASIANPAINT.NS", "NESTLEIND.NS"],
}
 
# ─────────────────────────────────────────────
# CACHE STORES
# ─────────────────────────────────────────────
 
_index_cache:     Dict[str, Tuple[List, float]] = {}   # index_name → (data, timestamp)
_sentiment_cache: Dict[str, Tuple[float, float]] = {}  # ticker     → (score, timestamp)
_sector_ma_cache: Dict[str, Tuple[float, float]] = {}  # sector_key → (score, timestamp)
_finbert_pipeline = None                               # lazy-loaded once
 
 
# ─────────────────────────────────────────────
# LAYER 0 — STOCK UNIVERSE
# ─────────────────────────────────────────────
 
def fetch_index_constituents(
    index_name: str = "nifty200",
    ttl_seconds: int = 86400,
) -> List[Dict[str, str]]:
    """
    Fetch live index constituents from NSE official CSVs.
    Caches for 24 h. Falls back to stale cache on network error.
    Returns list of {ticker, name, sector} dicts.
    """
    now = time.time()
    if index_name in _index_cache:
        data, fetched_at = _index_cache[index_name]
        if now - fetched_at < ttl_seconds:
            return data
 
    url = INDEX_URLS.get(index_name, INDEX_URLS["nifty200"])
    try:
        resp = httpx.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
 
        stocks = []
        for _, row in df.iterrows():
            ticker = str(row.get("Symbol", "")).strip()
            if not ticker:
                continue
            stocks.append({
                "ticker": f"{ticker}.NS",
                "name":   str(row.get("Company Name", ticker)).strip(),
                "sector": str(row.get("Industry", "Unknown")).strip().upper(),
            })
 
        _index_cache[index_name] = (stocks, now)
        return stocks
 
    except Exception as e:
        logger.warning(f"NSE CSV fetch failed ({index_name}): {e}")
        if index_name in _index_cache:
            return _index_cache[index_name][0]
        return []
 
 
def get_recommendation_pool(risk: str) -> List[Dict[str, str]]:
    """Map risk level → NSE index → live stock list."""
    return fetch_index_constituents(RISK_TO_INDEX.get(risk, "nifty200"))
 
 
# ─────────────────────────────────────────────
# LAYER 1 — NEWS SENTIMENT
# ─────────────────────────────────────────────
 
def _get_finbert():
    """Lazy-load FinBERT once. Returns None if transformers not installed."""
    global _finbert_pipeline
    if _finbert_pipeline is not None:
        return _finbert_pipeline
    try:
        from transformers import pipeline
        _finbert_pipeline = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            truncation=True,
            max_length=512,
        )
        logger.info("FinBERT loaded successfully.")
    except Exception as e:
        logger.warning(f"FinBERT unavailable (pip install transformers): {e}")
        _finbert_pipeline = None
    return _finbert_pipeline
 
 
def _finbert_score(headlines: List[str]) -> float:
    """
    Run FinBERT on a list of headlines.
    Returns normalised score: +1.0 = fully bullish, -1.0 = fully bearish.
    """
    model = _get_finbert()
    if not model or not headlines:
        return 0.0
 
    try:
        results = model(headlines[:15])  # cap to avoid slow inference
        total = 0.0
        for r in results:
            label, score = r["label"].lower(), r["score"]
            if label == "positive":
                total += score
            elif label == "negative":
                total -= score
            # neutral → 0
        return round(total / len(results), 4)
    except Exception as e:
        logger.warning(f"FinBERT inference error: {e}")
        return 0.0
 
 
def _marketaux_sentiment(ticker: str, api_key: str) -> Optional[float]:
    """
    Fetch news + sentiment from Marketaux (free: 100 req/day).
    Returns average sentiment_score [-1, +1] or None on failure.
    Get free key at: https://www.marketaux.com/
    """
    # Strip .NS suffix for Marketaux
    symbol = ticker.replace(".NS", "").replace(".BO", "")
    url = "https://api.marketaux.com/v1/news/all"
    params = {
        "symbols":         symbol,
        "filter_entities": "true",
        "language":        "en",
        "api_token":       api_key,
        "limit":           10,
    }
    try:
        resp = httpx.get(url, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json().get("data", [])
 
        scores = []
        for article in articles:
            for entity in article.get("entities", []):
                if entity.get("symbol", "").upper() == symbol.upper():
                    s = entity.get("sentiment_score")
                    if s is not None:
                        scores.append(float(s))
 
        return round(sum(scores) / len(scores), 4) if scores else None
    except Exception as e:
        logger.warning(f"Marketaux failed for {ticker}: {e}")
        return None
 
 
def _yfinance_news_sentiment(ticker: str) -> float:
    """
    Fallback: pull headlines from yfinance, score with FinBERT.
    Returns sentiment score [-1, +1].
    """
    try:
        import yfinance as yf
        info = yf.Ticker(ticker)
        news = info.news or []
        headlines = [
            n.get("content", {}).get("title", "")
            for n in news
            if n.get("content", {}).get("title")
        ]
        return _finbert_score(headlines)
    except Exception as e:
        logger.warning(f"yfinance news failed for {ticker}: {e}")
        return 0.0
 
 
def get_news_sentiment_score(
    ticker: str,
    marketaux_key: Optional[str] = None,
    ttl_seconds: int = 3600,   # refresh every hour
) -> float:
    """
    Main entry: returns news sentiment score [0, 1] (normalised for scoring).
    Priority: Marketaux API → yfinance + FinBERT → 0.5 (neutral fallback).
 
    Raw sentiment is [-1, +1]; we normalise to [0, 1] for the composite score.
    """
    now = time.time()
    if ticker in _sentiment_cache:
        score, fetched_at = _sentiment_cache[ticker]
        if now - fetched_at < ttl_seconds:
            return score
 
    raw = None
 
    # Try Marketaux first (pre-computed, fast)
    key = marketaux_key or os.getenv("MARKETAUX_API_KEY", "")
    if key:
        raw = _marketaux_sentiment(ticker, key)
 
    # Fallback to yfinance + FinBERT
    if raw is None:
        raw = _yfinance_news_sentiment(ticker)
 
    # Normalise [-1, +1] → [0, 1]
    normalised = round((raw + 1) / 2, 4)
 
    _sentiment_cache[ticker] = (normalised, now)
    return normalised
 
 
# ─────────────────────────────────────────────
# LAYER 2 — MACRO / SECTOR TREND
# ─────────────────────────────────────────────
 
def _sector_index_score(sector_key: str, ttl_seconds: int = 3600) -> float:
    """
    Checks if a sector's NSE index is above its 50-day moving average.
    Returns 0.0–1.0:
      1.0  = index well above 50-DMA (strong uptrend)
      0.5  = index near 50-DMA
      0.0  = index below 50-DMA (downtrend)
    """
    now = time.time()
    cache_key = f"sector_{sector_key}"
    if cache_key in _sector_ma_cache:
        score, fetched_at = _sector_ma_cache[cache_key]
        if now - fetched_at < ttl_seconds:
            return score
 
    yf_symbol = SECTOR_INDICES.get(sector_key.upper())
    if not yf_symbol:
        return 0.5  # unknown sector → neutral
 
    try:
        import yfinance as yf
        hist = yf.Ticker(yf_symbol).history(period="1y")
        if hist.empty or len(hist) < 50:
            return 0.5
 
        close = hist["Close"]
        sma50 = close.rolling(50).mean().iloc[-1]
        current = close.iloc[-1]
 
        # Distance above/below SMA50 as a fraction
        deviation = (current - sma50) / sma50  # e.g. +0.05 = 5% above
        # Map deviation [-0.10, +0.10] → [0, 1]
        score = float(np.clip((deviation + 0.10) / 0.20, 0.0, 1.0))
        score = round(score, 4)
    except Exception as e:
        logger.warning(f"Sector index fetch failed ({sector_key}): {e}")
        score = 0.5
 
    _sector_ma_cache[cache_key] = (score, now)
    return score
 
 
def _theme_bonus(ticker: str) -> float:
    """
    Returns a bonus [0, 0.2] if the ticker is part of a current macro theme.
    Themes represent structural tailwinds (policy, budget, global trends).
    """
    for theme_tickers in MACRO_THEMES.values():
        if ticker in theme_tickers:
            return 0.2
    return 0.0
 
 
def get_macro_trend_score(ticker: str, sector: str) -> float:
    """
    Combines:
      - Sector index trend (is the whole sector moving?) → 0–0.8
      - Macro theme bonus (is this a structural story?)  → 0–0.2
    Returns [0, 1].
    """
    sector_score  = _sector_index_score(sector) * 0.8
    theme_bonus   = _theme_bonus(ticker)
    return round(min(sector_score + theme_bonus, 1.0), 4)
 
 
# ─────────────────────────────────────────────
# LAYER 3 — FUNDAMENTAL HEALTH
# ─────────────────────────────────────────────
 
def get_fundamental_score(stock_data: Dict[str, Any]) -> float:
    """
    Scores company fundamentals on 4 axes → returns [0, 1].
 
    Axes:
      1. Debt/Equity        — can't ride a boom while drowning in debt
      2. Revenue growth     — already growing → likely to keep going
      3. Earnings growth    — profitability trend
      4. Insider/promoter   — high holding → management conviction
    """
    score = 0.0
 
    # 1. Debt/Equity (lower = healthier)
    de = stock_data.get("debtToEquity") or stock_data.get("debt_to_equity") or 999
    if de < 0.3:    score += 0.30
    elif de < 0.8:  score += 0.20
    elif de < 1.5:  score += 0.10
    # de >= 1.5 → 0 points
 
    # 2. Revenue growth
    rev_growth = stock_data.get("revenueGrowth") or stock_data.get("revenue_growth") or 0.0
    if rev_growth > 0.20:   score += 0.25
    elif rev_growth > 0.10: score += 0.15
    elif rev_growth > 0.0:  score += 0.05
 
    # 3. Earnings growth
    earn_growth = (
        stock_data.get("earningsGrowth")
        or stock_data.get("earnings_growth")
        or 0.0
    )
    if earn_growth > 0.20:   score += 0.25
    elif earn_growth > 0.05: score += 0.15
    elif earn_growth > 0.0:  score += 0.05
 
    # 4. Promoter / insider holding
    insider = (
        stock_data.get("heldPercentInsiders")
        or stock_data.get("promoter_holding")
        or 0.0
    )
    if insider > 0.60:   score += 0.20
    elif insider > 0.40: score += 0.12
    elif insider > 0.20: score += 0.05
 
    return round(min(score, 1.0), 4)
 
 
# ─────────────────────────────────────────────
# LAYER 4 — TECHNICAL MOMENTUM
# ─────────────────────────────────────────────
 
def get_momentum_score(stock_data: Dict[str, Any]) -> float:
    """
    Price-action confirmation that the move has already started.
    Uses data already fetched by the batch-stats endpoint.
    Returns [0, 1].
 
    Signals:
      - 20-day price momentum (is it moving up?)
      - Distance from 52-week high (near highs = breakout candidate)
      - Volume ratio (smart money entering?)
      - RSI zone (not overbought yet)
    """
    score = 0.0
 
    current_price = stock_data.get("current_price", 0) or 0
    if not current_price:
        return 0.0
 
    # ── 20-day momentum (annualised_return is our proxy) ──
    momentum = stock_data.get("annualised_return", 0.0) or 0.0
    # Convert annualised to approximate 20-day
    momentum_20d = momentum / 12   # rough monthly equivalent
    if momentum_20d > 0.08:   score += 0.30
    elif momentum_20d > 0.03: score += 0.18
    elif momentum_20d > 0.0:  score += 0.08
 
    # ── 52-week high proximity ──
    high_52w = stock_data.get("fifty_two_week_high") or stock_data.get("yearHigh") or 0
    if high_52w and current_price:
        pct_from_high = current_price / high_52w
        if pct_from_high >= 0.95:    score += 0.25   # within 5% of 52w high — breakout zone
        elif pct_from_high >= 0.85:  score += 0.12
        elif pct_from_high >= 0.70:  score += 0.05
 
    # ── Volatility-adjusted RSI approximation ──
    # (real RSI comes from price history; here we approximate from return data)
    volatility = stock_data.get("annualised_volatility", 0.3) or 0.3
    rsi_approx = 50 + (momentum * 50)
    rsi_approx = float(np.clip(rsi_approx, 0, 100))
 
    # Best zone: RSI 40–65 — trending but not overbought
    if 40 <= rsi_approx <= 65:    score += 0.25
    elif 30 <= rsi_approx < 40:   score += 0.10   # oversold recovery
    elif rsi_approx > 70:         score -= 0.10   # overbought penalty
 
    # ── Volatility penalty for safe/moderate (erratic stocks score less) ──
    if volatility > 0.50:
        score -= 0.15
 
    return round(float(np.clip(score, 0.0, 1.0)), 4)
 
 
# ─────────────────────────────────────────────
# COMPOSITE SCORER
# ─────────────────────────────────────────────
 
def compute_composite_score(
    ticker: str,
    stock_data: Dict[str, Any],
    sector: str,
    risk: str,
    marketaux_key: Optional[str] = None,
) -> Dict[str, float]:
    """
    Runs all 4 layers and returns individual + final weighted score.
    Returns dict with layer breakdowns for transparency.
    """
    news  = get_news_sentiment_score(ticker, marketaux_key)
    macro = get_macro_trend_score(ticker, sector)
    fund  = get_fundamental_score(stock_data)
    mom   = get_momentum_score(stock_data)
 
    # Apply risk-profile modifier:
    # Safe → amplify fundamental, dampen news (avoid reactive picks)
    # Aggressive → amplify news + momentum (chase the wave)
    if risk == "safe":
        weights = {**SCORE_WEIGHTS, "news_sentiment": 0.20, "fundamental": 0.40, "momentum": 0.10, "macro_trend": 0.30}
    elif risk == "aggressive":
        weights = {**SCORE_WEIGHTS, "news_sentiment": 0.45, "fundamental": 0.15, "momentum": 0.20, "macro_trend": 0.20}
    else:
        weights = SCORE_WEIGHTS
 
    final = round(
        weights["news_sentiment"] * news +
        weights["macro_trend"]    * macro +
        weights["fundamental"]    * fund +
        weights["momentum"]       * mom,
        4,
    )
 
    return {
        "final":          final,
        "news_sentiment": news,
        "macro_trend":    macro,
        "fundamental":    fund,
        "momentum":       mom,
    }
 
 
# ─────────────────────────────────────────────
# SIGNAL GENERATION (upgraded)
# ─────────────────────────────────────────────
 
def generate_trading_signal(
    current_price: float,
    sma_50: float,
    sma_200: float,
    rsi: float,
    momentum: float = 0.0,
    news_score: float = 0.5,    # NEW: sentiment-adjusted confidence
) -> Tuple[str, float]:
    """
    BUY/SELL/HOLD signal.
    News sentiment now adjusts confidence on top of technicals.
    """
    uptrend   = current_price > sma_50 > sma_200
    downtrend = current_price < sma_50 < sma_200
 
    rsi_overbought = rsi > 70
    rsi_oversold   = rsi < 30
 
    if uptrend and not rsi_overbought and momentum > 0:
        signal     = "BUY"
        confidence = min(0.95, 0.55 + (momentum * 0.15) + (news_score - 0.5) * 0.3)
    elif downtrend and not rsi_oversold:
        signal     = "SELL"
        confidence = min(0.90, 0.55 + (0.5 - news_score) * 0.3)
    elif rsi_overbought and news_score < 0.45:
        # Overbought AND negative news → stronger sell signal
        signal     = "SELL"
        confidence = 0.75
    elif rsi_oversold and news_score > 0.55:
        # Oversold BUT positive news → potential reversal buy
        signal     = "BUY"
        confidence = 0.65
    else:
        signal     = "HOLD"
        confidence = 0.50
 
    return signal, round(float(np.clip(confidence, 0.0, 1.0)), 2)
 
 
def calculate_targets_and_stoploss(
    current_price: float,
    volatility: float,
    duration: str,
    news_score: float = 0.5,   # strong positive news → wider target
) -> Dict[str, float]:
    """
    Target and stoploss adjusted for duration, volatility, and news momentum.
    """
    base_targets = {
        "short": 0.08,
        "mid":   0.12,
        "long":  0.18,
    }
    base_pct = base_targets.get(duration, 0.12)
 
    # Positive news momentum → slightly more ambitious target
    news_boost = (news_score - 0.5) * 0.10   # max ±5%
    vol_adj    = 1 + (volatility * 0.2)
    target_pct = (base_pct + news_boost) * vol_adj
 
    target    = round(current_price * (1 + target_pct), 2)
    stoploss  = round(current_price * (1 - max(0.04, volatility * 0.3)), 2)  # dynamic SL
 
    return {
        "target":     target,
        "stoploss":   stoploss,
        "upside_pct": round((target / current_price - 1) * 100, 2),
    }
 
 
# ─────────────────────────────────────────────
# FILTERING
# ─────────────────────────────────────────────
 
def filter_stocks_by_risk(
    stock_data_dict: Dict[str, Dict],
    risk: str,
) -> List[str]:
    """Filter stocks by risk profile criteria."""
    profile  = RISK_PROFILES.get(risk, RISK_PROFILES["moderate"])
    filtered = []
 
    for ticker, data in stock_data_dict.items():
        market_cap = data.get("market_cap", 0) or 0
        volatility = data.get("annualised_volatility", 0.5) or 0.5
 
        if not market_cap or volatility is None:
            continue
        if market_cap < profile["min_market_cap"]:
            continue
        if volatility > profile["max_volatility"]:
            continue
 
        filtered.append(ticker)
 
    return filtered
 
 
def get_sector_tickers(
    sector: Optional[str],
    stock_pool: List[Dict[str, str]],
) -> List[str]:
    """Filter tickers by sector from live pool (fuzzy match)."""
    if not sector or sector == "All":
        return [s["ticker"] for s in stock_pool]
 
    sector_lower = sector.lower()
    matched = [s["ticker"] for s in stock_pool if sector_lower in s.get("sector", "").lower()]
    return matched if matched else [s["ticker"] for s in stock_pool]
 
 
# ─────────────────────────────────────────────
# MAIN RECOMMENDATION BUILDER
# ─────────────────────────────────────────────
 
def build_recommendations(
    tickers: List[str],
    stock_data_dict: Dict[str, Dict],
    risk: str,
    duration: str,
    stock_pool: Optional[List[Dict[str, str]]] = None,
    sector: Optional[str] = None,
    capital: Optional[float] = None,
    limit: int = 8,
    marketaux_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Build final recommendation list using the 4-layer composite score.
 
    Each recommendation includes:
      - signal, confidence (news-adjusted)
      - target, stoploss (sentiment-adjusted)
      - invested capital projection for the timeframe
      - score breakdown per layer (for UI transparency)
      - news_catalyst: the reason why this stock is highlighted
    """
 
    # ── Sector pre-filter ──
    filtered_tickers = tickers
    if sector and sector != "All" and stock_pool:
        sector_tickers  = get_sector_tickers(sector, stock_pool)
        filtered_tickers = [t for t in tickers if t in sector_tickers]
 
    # ── Build sector lookup from pool ──
    sector_map: Dict[str, str] = {}
    name_map:   Dict[str, str] = {}
    if stock_pool:
        for item in stock_pool:
            sector_map[item["ticker"]] = item.get("sector", "Unknown")
            name_map[item["ticker"]]   = item.get("name", item["ticker"])
 
    recommendations = []
 
    for ticker in filtered_tickers:
        if ticker not in stock_data_dict:
            continue
 
        data          = stock_data_dict[ticker]
        current_price = data.get("current_price", 0)
        if not current_price:
            continue
 
        ticker_sector = sector_map.get(ticker, data.get("sector", "Unknown"))
 
        # ── 4-layer composite score ──
        scores = compute_composite_score(
            ticker, data, ticker_sector, risk, marketaux_key
        )
 
        # ── Derive SMAs from volatility (approximation until real OHLC is passed) ──
        vol   = data.get("annualised_volatility", 0.2) or 0.2
        sma50 = current_price * (1 - vol * 0.5)
        sma200= current_price * (1 - vol)
        rsi   = float(np.clip(50 + data.get("annualised_return", 0) * 50, 0, 100))
 
        signal, confidence = generate_trading_signal(
            current_price, sma50, sma200, rsi,
            momentum=data.get("annualised_return", 0),
            news_score=scores["news_sentiment"],
        )
 
        targets = calculate_targets_and_stoploss(
            current_price, vol, duration,
            news_score=scores["news_sentiment"],
        )
 
        duration_text = {
            "short": "1-3 months",
            "mid":   "3-6 months",
            "long":  "1-2 years",
        }.get(duration, "3-6 months")
 
        # ── News catalyst label (human-readable reason) ──
        catalyst = _derive_catalyst(ticker, ticker_sector, scores)
 
        rec = {
            "ticker":        ticker,
            "name":          name_map.get(ticker, data.get("name", ticker)),
            "price":         round(current_price, 2),
            "signal":        signal,
            "target":        targets["target"],
            "stoploss":      targets["stoploss"],
            "upside_pct":    targets["upside_pct"],
            "holding_period":duration_text,
            "confidence":    confidence,
 
            # ── composite score + breakdown ──
            "score":         scores["final"],
            "score_breakdown": {
                "news":        scores["news_sentiment"],
                "macro":       scores["macro_trend"],
                "fundamental": scores["fundamental"],
                "momentum":    scores["momentum"],
            },
 
            # ── why this stock ──
            "news_catalyst": catalyst,
 
            # ── legacy fields ──
            "returns_6m":    round(data.get("annualised_return", 0) * 100, 2),
            "volatility":    round(vol * 100, 2),
            "market_cap_cr": data.get("market_cap", "N/A"),
            "sector":        ticker_sector,
        }
 
        recommendations.append(rec)
 
    # Sort by composite score
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    final_recs = recommendations[:limit]

    if capital and capital > 0 and final_recs:
        allocated_amount = round(capital / len(final_recs), 2)
        for rec in final_recs:
            projected_value = round(allocated_amount * rec["target"] / rec["price"], 2)
            rec["allocated_capital"] = allocated_amount
            rec["projected_value_at_target"] = projected_value
            rec["expected_gain_amount"] = round(projected_value - allocated_amount, 2)
            rec["expected_gain_pct"] = rec["upside_pct"]

    return final_recs
 
 
# ─────────────────────────────────────────────
# HELPER — CATALYST LABEL
# ─────────────────────────────────────────────
 
def _derive_catalyst(
    ticker: str,
    sector: str,
    scores: Dict[str, float],
) -> str:
    """
    Generate a human-readable reason string explaining why this stock scored well.
    Used in the frontend recommendation card as 'Why this stock?'
    """
    parts = []
 
    if scores["news_sentiment"] >= 0.65:
        parts.append("🟢 Positive news flow")
    elif scores["news_sentiment"] <= 0.35:
        parts.append("🔴 Negative news — caution")
 
    if scores["macro_trend"] >= 0.70:
        # Check if in a named theme
        for theme_name, theme_tickers in MACRO_THEMES.items():
            if ticker in theme_tickers:
                parts.append(f"🚀 {theme_name} theme tailwind")
                break
        else:
            parts.append(f"📈 {sector} sector in uptrend")
 
    if scores["fundamental"] >= 0.65:
        parts.append("💪 Strong fundamentals")
 
    if scores["momentum"] >= 0.65:
        parts.append("⚡ Price momentum building")
    elif scores["momentum"] <= 0.25:
        parts.append("⚠️ Price not yet confirming")
 
    return " · ".join(parts) if parts else "📊 Quantitative screen pick"
