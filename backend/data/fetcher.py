import yfinance as yf
import pandas as pd
import numpy as np
from cachetools import TTLCache, cached
from cachetools.keys import hashkey
import os

CACHE_TTL = int(os.getenv("YFINANCE_CACHE_TTL", 900))  # 15 min default

_price_cache = TTLCache(maxsize=128, ttl=CACHE_TTL)
_meta_cache = TTLCache(maxsize=128, ttl=CACHE_TTL)


def normalize_symbol(ticker: str) -> str:
    symbol = ticker.strip().upper().replace("$", "")
    if not symbol:
        return symbol
    if symbol.endswith(".NS") or symbol.endswith(".BO") or symbol.endswith(".NSE") or symbol.endswith(".AX") or symbol.endswith(".L"):
        return symbol
    return symbol


def _ticker_variants(ticker: str) -> list[str]:
    symbol = normalize_symbol(ticker)
    variants = [symbol]
    if "." not in symbol and symbol.isalpha():
        variants.extend([f"{symbol}.NS", f"{symbol}.BO"])
    return variants


def _get_ticker_obj(ticker: str):
    return yf.Ticker(ticker.upper())


def _try_history(symbol: str, period: str = "1y") -> pd.DataFrame:
    try:
        t = _get_ticker_obj(symbol)
        return t.history(period=period, auto_adjust=True)
    except Exception:
        return pd.DataFrame()


def _safe_info(ticker_obj):
    try:
        return getattr(ticker_obj, "info", {}) or {}
    except Exception:
        return {}


def fetch_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Returns daily adjusted close prices for the last `period`."""
    for symbol in _ticker_variants(ticker):
        key = hashkey(symbol, period)
        if key in _price_cache:
            return _price_cache[key]

        df = _try_history(symbol, period)
        if df.empty:
            continue

        result = df[["Close"]].rename(columns={"Close": symbol})
        _price_cache[key] = result
        return result

    return pd.DataFrame()


def fetch_returns(tickers: list[str], period: str = "1y") -> tuple[pd.DataFrame, list[str], list[str]]:
    """Returns a DataFrame of daily % returns for valid tickers, plus valid and invalid ticker lists."""
    frames = []
    valid_tickers = []
    invalid_tickers = []

    for ticker in tickers:
        prices = fetch_price_history(ticker, period)
        if not prices.empty:
            frames.append(prices)
            valid_tickers.append(prices.columns[0])
        else:
            invalid_tickers.append(ticker.strip().upper())

    if not frames:
        raise ValueError("No valid price data found for any provided ticker")

    combined = pd.concat(frames, axis=1).dropna(how="all")
    if combined.empty:
        raise ValueError("No overlapping price data found for the provided valid tickers")

    returns = combined.pct_change().dropna()
    return returns, valid_tickers, invalid_tickers


@cached(_meta_cache, key=lambda ticker: hashkey(ticker))
def fetch_stock_meta(ticker: str) -> dict:
    """Returns metadata for a ticker, using fallback values when yfinance info is incomplete."""
    for symbol in _ticker_variants(ticker):
        info = _safe_info(_get_ticker_obj(symbol))
        name = info.get("longName") or info.get("shortName") or symbol
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")

        if current_price is None:
            hist = _try_history(symbol, "1mo")
            if not hist.empty:
                current_price = float(hist["Close"].iloc[-1])

        if current_price is None:
            continue

        history_1y = _try_history(symbol, "1y")
        fifty_two_high = info.get("fiftyTwoWeekHigh")
        fifty_two_low = info.get("fiftyTwoWeekLow")
        if history_1y is not None and not history_1y.empty:
            fifty_two_high = fifty_two_high or float(history_1y["Close"].max())
            fifty_two_low = fifty_two_low or float(history_1y["Close"].min())

        result = {
            "ticker": symbol,
            "name": name,
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "current_price": current_price,
            "52w_high": fifty_two_high or 0,
            "52w_low": fifty_two_low or 0,
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", None),
            "currency": info.get("currency", "USD"),
        }
        return result

    raise ValueError(f"Ticker not found or delisted: {ticker}")


def compute_annualised_stats(returns: pd.DataFrame) -> dict:
    """Returns annualised mean return and volatility per ticker."""
    ann_return = returns.mean() * 252
    ann_vol = returns.std() * np.sqrt(252)
    return {
        "annualised_return": ann_return.to_dict(),
        "annualised_volatility": ann_vol.to_dict(),
    }