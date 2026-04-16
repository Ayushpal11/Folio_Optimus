from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv
import os
load_dotenv()

import numpy as np
import pandas as pd
import yfinance as yf
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypfopt import EfficientFrontier, risk_models, expected_returns
from pypfopt.discrete_allocation import DiscreteAllocation

from data.fetcher import (
    normalize_symbol,
    fetch_stock_meta,
    fetch_returns,
    compute_annualised_stats,
    fetch_price_history,
    fetch_analyst_data,
    search_stocks,
    analyze_folio,
)
from data.recommendation import (
    get_recommendation_pool,
    filter_stocks_by_risk,
    get_sector_tickers,
    build_recommendations,
)
from app.upstox.routes import router as upstox_router
from app.backtest import backtest_signal, calculate_win_rate
from app.rate_limit import limiter

import uvicorn

app = FastAPI(title="Portfolio Optimizer API", version="2.0.0")

# Add rate limiter to app
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your frontend origin for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upstox_router, prefix="/api/upstox")

class OptimizeRequest(BaseModel):
    tickers: List[str]
    capital: float
    risk_tolerance: str = "medium"  # low / medium / high

class BatchRequest(BaseModel):
    tickers: List[str]

class HoldingItem(BaseModel):
    ticker: str
    qty: float
    avg_price: float
    exchange: str = "NSE"

class FolioRequest(BaseModel):
    holdings: List[HoldingItem]

class RecommendationRequest(BaseModel):
    risk: str  # "safe", "moderate", "aggressive"
    duration: str  # "short", "mid", "long"
    sector: str = "All"  # Optional sector filter
    capital: float = None  # Optional capital amount

class BacktestRequest(BaseModel):
    signal: str  # "BUY", "SELL", "HOLD"
    entry_date: str  # "YYYY-MM-DD"
    target_price: float
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None

@app.get("/")
def root():
    return {"status": "ok", "message": "Portfolio Optimizer API. Use /api/* endpoints."}

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0"}

@app.get("/api/search")
def search(q: str):
    """
    Fuzzy search by stock symbol or company name.
    Example: /api/search?q=reliance
    """
    if len(q.strip()) < 1:
        return {"results": []}
    return {"results": search_stocks(q)}

@app.get("/api/analyst/{ticker}")
def get_analyst_data(ticker: str):
    try:
        return fetch_analyst_data(ticker)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

@app.post("/api/folio/analyze")
def analyze_portfolio(req: FolioRequest):
    if not req.holdings:
        raise HTTPException(status_code=400, detail="No holdings provided")
    try:
        return analyze_folio([h.dict() for h in req.holdings])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

@app.post("/api/optimize")
async def optimize(req: OptimizeRequest):
    """
    Markowitz portfolio optimization using Efficient Frontier.
    
    Request:
    {
      "tickers": ["AAPL", "MSFT", "GOOGL"],
      "capital": 100000,
      "risk_tolerance": "low" | "medium" | "high"
    }
    
    Returns: Optimized weights, discrete allocation (share counts), performance metrics
    """
    if not req.tickers:
        raise HTTPException(status_code=400, detail="No tickers provided")
    
    if req.capital <= 0:
        raise HTTPException(status_code=400, detail="Capital must be positive")
    
    try:
        # Normalize tickers
        tickers_normalized = [normalize_symbol(t) for t in req.tickers]
        
        # 1. Fetch 1-year daily closes
        prices = yf.download(tickers_normalized, period="1y")["Close"].dropna()
        
        if prices.empty or len(prices) < 30:
            raise ValueError("Insufficient price history for optimization")
        
        # Handle single ticker (yfinance returns Series instead of DataFrame)
        if isinstance(prices, pd.Series):
            prices = prices.to_frame()
        
        # 2. Compute expected returns and covariance matrix
        mu = expected_returns.mean_historical_return(prices)
        S = risk_models.sample_cov(prices)
        
        # 3. Run Markowitz optimization based on risk tolerance
        ef = EfficientFrontier(mu, S)
        
        if req.risk_tolerance.lower() == "low":
            # Minimize volatility
            ef.min_volatility()
        elif req.risk_tolerance.lower() == "high":
            # Maximize Sharpe ratio for aggressive growth
            ef.max_sharpe()
        else:
            # Medium: Quadratic utility (balanced risk-return)
            ef.max_quadratic_utility(risk_aversion=1.0)
        
        weights = ef.clean_weights()
        perf = ef.portfolio_performance(verbose=False)  # (return, vol, sharpe)
        
        # 4. Discrete allocation (how many shares to buy)
        latest_prices = prices.iloc[-1]
        
        # Ensure weights dict keys match latest_prices index
        weights_aligned = {ticker: weights.get(ticker, 0) for ticker in latest_prices.index}
        
        da = DiscreteAllocation(weights_aligned, latest_prices, total_portfolio_value=req.capital)
        allocation, leftover = da.greedy_portfolio()
        
        # Calculate total value and allocation details
        allocation_details = []
        total_allocated = 0
        
        for ticker, shares in allocation.items():
            price = latest_prices.get(ticker, 0)
            value = shares * price
            total_allocated += value
            allocation_details.append({
                "ticker": ticker,
                "shares": shares,
                "price": round(float(price), 2),
                "value": round(float(value), 2),
                "weight": round(weights_aligned.get(ticker, 0) * 100, 2)
            })
        
        return {
            "optimization_status": "success",
            "risk_tolerance": req.risk_tolerance,
            "weights": {k: round(v, 4) for k, v in weights.items()},
            "allocation": allocation_details,
            "total_allocated": round(total_allocated, 2),
            "leftover_cash": round(leftover, 2),
            "performance": {
                "expected_annual_return": round(perf[0], 4),
                "annual_volatility": round(perf[1], 4),
                "sharpe_ratio": round(perf[2], 4)
            },
            "input_capital": req.capital,
            "diversification": len(allocation)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Optimization failed: {str(e)}")

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

@app.post("/api/recommend")
def get_recommendations(req: RecommendationRequest):
    """
    Get AI-powered stock recommendations based on risk profile.
    Pulls live stock universe from NSE index CSVs.
    
    Request:
    {
      "risk": "safe|moderate|aggressive",
      "duration": "short|mid|long",
      "sector": "All|IT|Banking|Pharma|etc",
      "capital": optional number
    }
    
    Returns: List of recommended stocks with signals, targets, stoploss
    """
    try:
        # Validate inputs
        if req.risk not in ["safe", "moderate", "aggressive"]:
            raise ValueError("Risk must be 'safe', 'moderate', or 'aggressive'")
        if req.duration not in ["short", "mid", "long"]:
            raise ValueError("Duration must be 'short', 'mid', or 'long'")

        # Get live stock pool from NSE index based on risk profile
        stock_pool = get_recommendation_pool(req.risk)
        
        if not stock_pool:
            raise ValueError(f"Unable to fetch stocks for risk profile '{req.risk}' from NSE")

        # Apply sector filter if specified (using live pool data)
        if req.sector and req.sector != "All":
            sector_tickers = get_sector_tickers(req.sector, stock_pool)
            stock_pool = [s for s in stock_pool if s["ticker"] in sector_tickers]

            if not stock_pool:
                raise ValueError(f"No stocks found in sector '{req.sector}' for risk profile '{req.risk}'")

        # Fetch detailed data for all stocks in pool (limit to 100 to avoid timeout)
        tickers_to_fetch = [s["ticker"] for s in stock_pool[:100]]
        returns, valid_tickers, invalid_tickers = fetch_returns(tickers_to_fetch, period="1y")
        
        if not valid_tickers:
            raise ValueError("Unable to fetch data for stocks in this category")

        stats = compute_annualised_stats(returns)

        # Build stock data dict with enriched data
        stock_data_dict = {}
        for ticker in valid_tickers:
            try:
                meta = fetch_stock_meta(ticker)
                stock_data_dict[ticker] = {
                    **meta,
                    "annualised_return": stats["annualised_return"].get(ticker, 0),
                    "annualised_volatility": stats["annualised_volatility"].get(ticker, 0.2),
                }
            except Exception:
                # Skip stocks where we can't fetch meta data
                continue

        # Filter by risk criteria and build recommendations
        filtered_tickers = filter_stocks_by_risk(stock_data_dict, req.risk)
        recommendations = build_recommendations(
            filtered_tickers,
            stock_data_dict,
            req.risk,
            req.duration,
            stock_pool=stock_pool,
            sector=req.sector if req.sector != "All" else None,
            capital=req.capital,
            limit=8,
        )

        return {
            "risk_profile": req.risk,
            "duration": req.duration,
            "sector": req.sector or "All",
            "pool_size": len(stock_pool),
            "fetched": len(valid_tickers),
            "recommendations": recommendations,
            "count": len(recommendations),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=f"Recommendation engine failed: {str(e)}")

@app.post("/api/backtest/{ticker}")
@limiter.limit("10/minute")
async def backtest(request: Request, ticker: str, req: BacktestRequest):
    """
    Backtest a trading signal.
    
    Returns P&L metrics for a historical signal.
    """
    try:
        result = backtest_signal(
            ticker=ticker,
            signal=req.signal,
            entry_date=req.entry_date,
            target_price=req.target_price,
            entry_price=req.entry_price,
            stop_loss=req.stop_loss,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Backtest failed: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
