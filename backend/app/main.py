from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv
import os
load_dotenv()

import numpy as np
import pandas as pd
import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pypfopt import EfficientFrontier, risk_models, expected_returns

from data.fetcher import normalize_symbol, fetch_stock_meta, fetch_returns, compute_annualised_stats, fetch_price_history

import uvicorn

app = FastAPI(title="Portfolio Optimizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://folio-optimus.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OptimizeRequest(BaseModel):
    tickers: List[str]
    capital: float
    risk_tolerance: str = "medium"  # low / medium / high

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}

@app.post("/api/optimize")
def optimize(req: OptimizeRequest):
    # Stub — real logic comes in Phase 3
    return {
        "tickers": req.tickers,
        "capital": req.capital,
        "weights": {t: round(1/len(req.tickers), 4) for t in req.tickers},
        "expected_return": 0.12,
        "volatility": 0.18,
        "sharpe_ratio": 0.67,
        "ai_advice": "Mock response — AI integration coming in Phase 4"
    }

@app.get("/api/stock/{ticker}")
def get_stock_info(ticker: str):
    """Single stock metadata + 1Y stats."""
    try:
        symbol = normalize_symbol(ticker)
        meta = fetch_stock_meta(symbol)
        returns, valid_tickers, invalid_tickers = fetch_returns([symbol], period="1y")
        resolved_symbol = valid_tickers[0]
        stats = compute_annualised_stats(returns)
        return {
            **meta,
            "annualised_return":     round(stats["annualised_return"][resolved_symbol], 4),
            "annualised_volatility": round(stats["annualised_volatility"][resolved_symbol], 4),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Data fetch failed: {str(e)}")

@app.get("/api/price-history/{ticker}")
def get_price_history(ticker: str, period: str = "1y"):
    """
    Returns a flat list of daily closing prices for sparkline charts.
    Example: GET /api/price-history/RELIANCE.NS
    """
    try:
        symbol = normalize_symbol(ticker)
        df = fetch_price_history(symbol, period)
        if df.empty:
            raise ValueError(f"No price history found for ticker: {ticker}")

        resolved_symbol = df.columns[0]
        prices = df[resolved_symbol].dropna().round(2).tolist()
        dates = df.index.strftime("%Y-%m-%d").tolist()
        return {
            "ticker": resolved_symbol,
            "prices": prices,
            "dates": dates,
            "period": period,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Price history fetch failed: {str(e)}")

@app.post("/api/batch-stats")
def get_batch_stats(req: dict):
    """Returns returns matrix + stats for a list of tickers."""
    raw_tickers = [t.strip() for t in req.get("tickers", []) if t and t.strip()]
    if not raw_tickers:
        raise HTTPException(status_code=400, detail="No tickers provided")

    tickers = [normalize_symbol(t) for t in raw_tickers]
    try:
        returns, valid_tickers, invalid_tickers = fetch_returns(tickers, period="1y")
        stats = compute_annualised_stats(returns)
        corr = returns.corr().round(4).to_dict()
        response = {
            "tickers":               valid_tickers,
            "invalid_tickers":       invalid_tickers,
            "annualised_return":     {k: round(v, 4) for k, v in stats["annualised_return"].items()},
            "annualised_volatility": {k: round(v, 4) for k, v in stats["annualised_volatility"].items()},
            "correlation_matrix":    corr,
            "data_points":           len(returns),
        }
        if invalid_tickers:
            response["warning"] = f"Some tickers were invalid or had no valid history: {', '.join(invalid_tickers)}"
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Batch fetch failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
