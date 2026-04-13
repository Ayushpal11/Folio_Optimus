import os
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf
from cachetools import TTLCache, cached
from cachetools.keys import hashkey

from app.upstox.client import UpstoxClient
from app.utils.ticker_mapper import get_instrument_key

CACHE_TTL = int(os.getenv("YFINANCE_CACHE_TTL", 900))  # 15 min default
UPSTOX_ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")

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


def _get_upstox_client() -> Optional[UpstoxClient]:
    if not UPSTOX_ACCESS_TOKEN:
        return None
    try:
        return UpstoxClient(UPSTOX_ACCESS_TOKEN)
    except Exception:
        return None


def _upstox_ltp(symbol: str) -> Optional[float]:
    try:
        client = _get_upstox_client()
        instrument_key = get_instrument_key(symbol)
        if not client or not instrument_key:
            return None

        data = client.get_ltp(instrument_key)
        if not data:
            return None

        payload = data.get("data") if isinstance(data, dict) else data
        if isinstance(payload, dict):
            for key in ("ltp", "LTP", "last_price", "lastTradedPrice", "price"):
                value = payload.get(key)
                if value is not None:
                    return float(value)
    except Exception:
        pass
    return None


def _upstox_candle_list(response: dict) -> list:
    if not response:
        return []
    data = response.get("data") if isinstance(response, dict) else response
    if isinstance(data, dict) and "candles" in data:
        data = data["candles"]
    if isinstance(data, list):
        return data
    return []


def _estimate_start_date(period: str) -> str:
    today = datetime.utcnow().date()
    if period.endswith("y"):
        years = int(period[:-1] or 1)
        start = today - timedelta(days=365 * years)
    elif period.endswith("mo"):
        months = int(period[:-2] or 1)
        start = today - timedelta(days=30 * months)
    else:
        start = today - timedelta(days=365)
    return start.strftime("%Y-%m-%d")


def _try_upstox_history(symbol: str, period: str = "1y") -> pd.DataFrame:
    try:
        client = _get_upstox_client()
        instrument_key = get_instrument_key(symbol)
        if not client or not instrument_key:
            return pd.DataFrame()

        from_date = _estimate_start_date(period)
        to_date = datetime.utcnow().strftime("%Y-%m-%d")
        response = client.get_historical(instrument_key, interval="day", from_date=from_date, to_date=to_date)
        candles = _upstox_candle_list(response)
        if not candles:
            return pd.DataFrame()

        rows = []
        for item in candles:
            if len(item) < 5:
                continue
            date_value = item[0]
            close = item[4]
            try:
                rows.append((date_value, float(close)))
            except Exception:
                continue

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=["date", "Close"])
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").sort_index()
        return df
    except Exception:
        return pd.DataFrame()

SEARCH_INDEX = [
    {"ticker": "RELIANCE.NS", "name": "Reliance Industries Ltd", "exchange": "NSE"},
    {"ticker": "RELIANCE.BO", "name": "Reliance Industries Ltd", "exchange": "BSE"},
    {"ticker": "TCS.NS", "name": "Tata Consultancy Services Ltd", "exchange": "NSE"},
    {"ticker": "TCS.BO", "name": "Tata Consultancy Services Ltd", "exchange": "BSE"},
    {"ticker": "HDFCBANK.NS", "name": "HDFC Bank Ltd", "exchange": "NSE"},
    {"ticker": "HDFCBANK.BO", "name": "HDFC Bank Ltd", "exchange": "BSE"},
    {"ticker": "INFY.NS", "name": "Infosys Ltd", "exchange": "NSE"},
    {"ticker": "INFY.BO", "name": "Infosys Ltd", "exchange": "BSE"},
    {"ticker": "ICICIBANK.NS", "name": "ICICI Bank Ltd", "exchange": "NSE"},
    {"ticker": "ICICIBANK.BO", "name": "ICICI Bank Ltd", "exchange": "BSE"},
    {"ticker": "HINDUNILVR.NS", "name": "Hindustan Unilever Ltd", "exchange": "NSE"},
    {"ticker": "HINDUNILVR.BO", "name": "Hindustan Unilever Ltd", "exchange": "BSE"},
    {"ticker": "SBIN.NS", "name": "State Bank of India", "exchange": "NSE"},
    {"ticker": "SBIN.BO", "name": "State Bank of India", "exchange": "BSE"},
    {"ticker": "BHARTIARTL.NS", "name": "Bharti Airtel Ltd", "exchange": "NSE"},
    {"ticker": "BHARTIARTL.BO", "name": "Bharti Airtel Ltd", "exchange": "BSE"},
    {"ticker": "ITC.NS", "name": "ITC Ltd", "exchange": "NSE"},
    {"ticker": "ITC.BO", "name": "ITC Ltd", "exchange": "BSE"},
    {"ticker": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank Ltd", "exchange": "NSE"},
    {"ticker": "KOTAKBANK.BO", "name": "Kotak Mahindra Bank Ltd", "exchange": "BSE"},
    {"ticker": "AAPL", "name": "Apple Inc.", "exchange": "US"},
    {"ticker": "MSFT", "name": "Microsoft Corporation", "exchange": "US"},
    {"ticker": "GOOGL", "name": "Alphabet Inc.", "exchange": "US"},
    {"ticker": "NVDA", "name": "NVIDIA Corporation", "exchange": "US"},
    {"ticker": "META", "name": "Meta Platforms, Inc.", "exchange": "US"},
    {"ticker": "AMZN", "name": "Amazon.com, Inc.", "exchange": "US"},
    {"ticker": "TSLA", "name": "Tesla, Inc.", "exchange": "US"},
    {"ticker": "AMD", "name": "Advanced Micro Devices, Inc.", "exchange": "US"},
    {"ticker": "INTC", "name": "Intel Corporation", "exchange": "US"},
    {"ticker": "CRM", "name": "Salesforce, Inc.", "exchange": "US"},
]


def _get_ticker_obj(ticker: str):
    return yf.Ticker(ticker.upper())


def _search_matches(query: str) -> list[dict]:
    q = query.strip().lower()
    if not q:
        return []

    exact = [item for item in SEARCH_INDEX if item["ticker"].lower() == q or item["ticker"].lower().replace(".ns", "") == q or item["ticker"].lower().replace(".bo", "") == q]
    if exact:
        return exact[:10]

    tokens = q.split()
    results = []
    for item in SEARCH_INDEX:
        name = item["name"].lower()
        ticker = item["ticker"].lower()
        if q in ticker or q in name or all(token in name for token in tokens):
            results.append(item)
    return results[:15]


def search_stocks(query: str, limit: int = 15) -> list[dict]:
    candidates = _search_matches(query)
    if candidates:
        return candidates[:limit]

    mapped_key = get_instrument_key(query)
    if mapped_key:
        return [{"ticker": query.strip().upper(), "name": query.strip().title(), "exchange": "NSE"}]

    # fallback exact lookup using yfinance if the query looks like a valid symbol
    if query and query.isalpha() and len(query) <= 5:
        symbol = normalize_symbol(query)
        info = _safe_info(_get_ticker_obj(symbol))
        if info.get("currentPrice") or info.get("regularMarketPrice"):
            return [{"ticker": symbol, "name": info.get("longName") or info.get("shortName") or symbol, "exchange": "US"}]

    return []


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

        # Try Upstox first for mapped symbols
        clean_symbol = symbol.replace(".NS", "").replace(".BO", "").upper()
        if get_instrument_key(clean_symbol):
            df = _try_upstox_history(clean_symbol, period)
            if not df.empty:
                result = df[["Close"]].rename(columns={"Close": symbol})
                _price_cache[key] = result
                return result

        # Fallback to yfinance
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
    """Returns metadata for a ticker, using Upstox first for mapped Indian stocks, then yfinance as fallback."""
    for symbol in _ticker_variants(ticker):
        # Try Upstox first for mapped symbols
        current_price = None
        instrument_key = get_instrument_key(symbol.replace(".NS", "").replace(".BO", "").upper())
        if instrument_key:
            upstox_price = _upstox_ltp(symbol.replace(".NS", "").replace(".BO", "").upper())
            if upstox_price:
                current_price = upstox_price

        # Fallback to yfinance if Upstox didn't work
        if current_price is None:
            info = _safe_info(_get_ticker_obj(symbol))
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")

        if current_price is None:
            hist = _try_upstox_history(symbol.replace(".NS", "").replace(".BO", "").upper(), "1mo")
            if not hist.empty:
                current_price = float(hist["Close"].iloc[-1])

        if current_price is None:
            hist = _try_history(symbol, "1mo")
            if not hist.empty:
                current_price = float(hist["Close"].iloc[-1])

        if current_price is None:
            continue

        # Get name from yfinance
        info = _safe_info(_get_ticker_obj(symbol))
        name = info.get("longName") or info.get("shortName") or symbol

        # Try Upstox history if symbol is mapped
        history_1y = pd.DataFrame()
        if instrument_key:
            history_1y = _try_upstox_history(symbol.replace(".NS", "").replace(".BO", "").upper(), "1y")
        if history_1y.empty:
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


def fetch_analyst_data(ticker: str) -> dict:
    """Returns analyst recommendation summary and recent published ratings."""
    symbol = normalize_symbol(ticker)
    for variant in _ticker_variants(symbol):
        ticker_obj = _get_ticker_obj(variant)
        info = _safe_info(ticker_obj)
        if not info:
            continue

        rec_key = info.get("recommendationKey") or info.get("recommendationMean") or "hold"
        target = info.get("targetMeanPrice") or info.get("targetLowPrice") or info.get("targetHighPrice")
        analysts = info.get("numberOfAnalystOpinions") or 0

        recommendations = []
        try:
            rec_df = ticker_obj.recommendations
            if rec_df is not None and not rec_df.empty:
                rec_df = rec_df.reset_index().sort_values(by="Date", ascending=False).head(6)
                for _, row in rec_df.iterrows():
                    recommendations.append({
                        "firm": row.get("Firm") or "Unknown",
                        "action": row.get("To Grade") or row.get("Action") or "—",
                        "from_grade": row.get("From Grade") or "—",
                        "to_grade": row.get("To Grade") or "—",
                        "date": row.get("Date").strftime("%Y-%m-%d") if hasattr(row.get("Date"), "strftime") else str(row.get("Date")),
                    })
        except Exception:
            recommendations = []

        return {
            "ticker": variant,
            "name": info.get("longName") or info.get("shortName") or variant,
            "recommendation": rec_key,
            "target_mean_price": target,
            "analyst_count": analysts,
            "recommendations": recommendations,
        }

    raise ValueError(f"Unable to fetch analyst data for ticker: {ticker}")


def analyze_folio(holdings: list[dict]) -> dict:
    """Return holdings analysis and buy/sell/hold guidance."""
    if not holdings:
        raise ValueError("No holdings provided")

    portfolio = []
    total_invested = 0.0
    total_current = 0.0

    for holding in holdings:
        raw_ticker = str(holding.get("ticker", "")).strip()
        qty = float(holding.get("qty", 0))
        avg_price = float(holding.get("avg_price", 0))
        exchange = holding.get("exchange", "NSE")

        if not raw_ticker or qty <= 0 or avg_price <= 0:
            raise ValueError("Each holding must include ticker, qty, and avg_price")

        # Allow stock name input by searching if needed
        ticker = normalize_symbol(raw_ticker)
        if "." not in ticker or ticker.upper() == ticker and not ticker.endswith((".NS", ".BO", ".L", ".AX")):
            results = search_stocks(raw_ticker)
            if results:
                chosen = next((item for item in results if item["exchange"] == exchange), results[0])
                ticker = normalize_symbol(chosen["ticker"])

        meta = fetch_stock_meta(ticker)
        current_price = meta["current_price"]
        invested_value = qty * avg_price
        current_value = qty * current_price
        pnl = current_value - invested_value
        pnl_pct = round((pnl / invested_value) * 100, 2) if invested_value else 0.0

        returns, valid_tickers, invalid_tickers = fetch_returns([ticker], period="1y")
        valid_symbol = valid_tickers[0] if valid_tickers else ticker
        stats = compute_annualised_stats(returns)
        ann_return = stats["annualised_return"].get(valid_symbol, 0.0)
        ann_vol = stats["annualised_volatility"].get(valid_symbol, 0.0)
        risk_reward = ann_return / (ann_vol or 1)

        action = "HOLD"
        reason = "Hold and monitor."
        if pnl_pct <= -12 and ann_return > 0.08:
            action = "BUY MORE"
            reason = "Good long-term outlook, consider averaging down carefully."
        elif pnl_pct <= -8 and ann_return <= 0.08:
            action = "SELL"
            reason = "Position is down and momentum is weak; reduce exposure."
        elif pnl_pct >= 20 and ann_return < 0.05:
            action = "BOOK PROFIT"
            reason = "Strong gains achieved while outlook is uncertain."
        elif ann_return > 0.15 and risk_reward > 0.7:
            action = "BUY"
            reason = "High expected return with favorable risk/reward."
        elif ann_return < 0 and pnl_pct < 0:
            action = "SELL"
            reason = "Negative outlook and currently underwater."
        elif pnl_pct > 8 and ann_return > 0.05:
            action = "HOLD"
            reason = "Healthy gains with positive outlook; hold for more upside."

        stop_loss = round(current_price * (1 - min(0.15, ann_vol * 0.5)), 2)
        target = round(current_price * (1 + min(0.3, ann_vol * 0.9 + 0.05)), 2)
        upside_to_target = round(((target - current_price) / current_price) * 100, 1) if current_price else 0

        portfolio.append({
            "input": raw_ticker,
            "ticker": valid_symbol,
            "name": meta.get("name", valid_symbol),
            "exchange": exchange,
            "qty": qty,
            "avg_price": avg_price,
            "current_price": current_price,
            "invested_value": round(invested_value, 2),
            "current_value": round(current_value, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "annualised_return": round(ann_return, 4),
            "annualised_volatility": round(ann_vol, 4),
            "signal": action,
            "reason": reason,
            "stop_loss": stop_loss,
            "target": target,
            "upside_to_target": upside_to_target,
        })

        total_invested += invested_value
        total_current += current_value

    summary = {
        "total_invested": round(total_invested, 2),
        "total_current": round(total_current, 2),
        "total_pnl": round(total_current - total_invested, 2),
        "total_pnl_pct": round(((total_current - total_invested) / total_invested) * 100, 2) if total_invested else 0.0,
        "num_holdings": len(portfolio),
    }

    # Overall portfolio status
    avg_return = sum(item["annualised_return"] for item in portfolio) / len(portfolio) if portfolio else 0
    avg_vol = sum(item["annualised_volatility"] for item in portfolio) / len(portfolio) if portfolio else 0
    total_pnl_pct = summary["total_pnl_pct"]

    if total_pnl_pct > 15 and avg_return > 0.08:
        portfolio_status = "GOOD"
        portfolio_reason = "Strong overall performance with positive returns."
    elif total_pnl_pct < -10 or avg_return < 0:
        portfolio_status = "BAD"
        portfolio_reason = "Underperforming with losses; consider rebalancing."
    else:
        portfolio_status = "STABLE"
        portfolio_reason = "Moderate performance; monitor for opportunities."

    summary["portfolio_status"] = portfolio_status
    summary["portfolio_reason"] = portfolio_reason

    return {
        "holdings": portfolio,
        "summary": summary,
    }
