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

from data.fetcher import fetch_stock_meta, fetch_returns, compute_annualised_stats

import uvicorn

app = FastAPI(title="Portfolio Optimizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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
        meta    = fetch_stock_meta(ticker)
        returns = fetch_returns([ticker], period="1y")
        stats   = compute_annualised_stats(returns)
        return {
            **meta,
            "annualised_return":     round(stats["annualised_return"][ticker.upper()], 4),
            "annualised_volatility": round(stats["annualised_volatility"][ticker.upper()], 4),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Data fetch failed: {str(e)}")


@app.post("/api/batch-stats")
def get_batch_stats(req: dict):
    """Returns returns matrix + stats for a list of tickers."""
    tickers = [t.strip().upper() for t in req.get("tickers", [])]
    if not tickers:
        raise HTTPException(status_code=400, detail="No tickers provided")
    try:
        returns = fetch_returns(tickers, period="1y")
        stats   = compute_annualised_stats(returns)
        corr    = returns.corr().round(4).to_dict()
        return {
            "tickers":               tickers,
            "annualised_return":     {k: round(v, 4) for k, v in stats["annualised_return"].items()},
            "annualised_volatility": {k: round(v, 4) for k, v in stats["annualised_volatility"].items()},
            "correlation_matrix":    corr,
            "data_points":           len(returns),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Batch fetch failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
