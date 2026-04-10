import yfinance as yf
import pandas as pd
import numpy as np
from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from datetime import datetime, timedelta
import os

CACHE_TTL = int(os.getenv("YFINANCE_CACHE_TTL", 900))  # 15 min default

_price_cache = TTLCache(maxsize=128, ttl=CACHE_TTL)
_meta_cache  = TTLCache(maxsize=128, ttl=CACHE_TTL)

def _get_ticker_obj(ticker: str):
    return yf.Ticker(ticker.upper())

def fetch_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Returns daily adjusted close prices for the last `period`."""
    key = hashkey(ticker, period)
    if key in _price_cache:
        return _price_cache[key]

    t = _get_ticker_obj(ticker)
    df = t.history(period=period, auto_adjust=True)

    if df.empty:
        return pd.DataFrame()  # Return empty DataFrame instead of raising

    result = df[["Close"]].rename(columns={"Close": ticker})
    _price_cache[key] = result
    return result

def fetch_returns(tickers: list[str], period: str = "1y") -> tuple[pd.DataFrame, list[str]]:
    """Returns a DataFrame of daily % returns for valid tickers and list of valid tickers."""
    frames = []
    valid_tickers = []
    for t in tickers:
        prices = fetch_price_history(t, period)
        if not prices.empty:
            frames.append(prices)
            valid_tickers.append(t.upper())

    if not frames:
        raise ValueError("No valid price data found for any ticker")

    combined = pd.concat(frames, axis=1).dropna(how="all")
    if combined.empty:
        raise ValueError("No overlapping price data found")

    returns = combined.pct_change().dropna()
    return returns, valid_tickers

@cached(_meta_cache, key=lambda ticker: hashkey(ticker))
def fetch_stock_meta(ticker: str) -> dict:
    """Returns metadata for a ticker."""
    t = _get_ticker_obj(ticker)
    info = t.info
    result = {
        "ticker":        ticker.upper(),
        "name":          info.get("longName", ticker),
        "sector":        info.get("sector", "Unknown"),
        "industry":      info.get("industry", "Unknown"),
        "current_price": info.get("currentPrice") or info.get("regularMarketPrice", 0),
        "52w_high":      info.get("fiftyTwoWeekHigh", 0),
        "52w_low":       info.get("fiftyTwoWeekLow", 0),
        "market_cap":    info.get("marketCap", 0),
        "pe_ratio":      info.get("trailingPE", None),
        "currency":      info.get("currency", "USD"),
    }

    return result

def compute_annualised_stats(returns: pd.DataFrame) -> dict:
    """Returns annualised mean return and volatility per ticker."""
    ann_return = returns.mean() * 252
    ann_vol    = returns.std() * np.sqrt(252)
    return {
        "annualised_return": ann_return.to_dict(),
        "annualised_volatility": ann_vol.to_dict(),
    }