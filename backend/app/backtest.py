import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from data.fetcher import normalize_symbol


def backtest_signal(
    ticker: str,
    signal: str,
    entry_date: str,
    target_price: float,
    entry_price: Optional[float] = None,
    stop_loss: Optional[float] = None,
) -> Dict:
    """
    Backtest a trading signal.
    
    Given a past BUY/SELL signal on entry_date,
    simulate holding until:
    - Target price hit
    - Stop loss hit (if specified)
    - 90 days passed
    
    Returns P&L metrics.
    """
    try:
        # Normalize ticker
        normalized_ticker = normalize_symbol(ticker)
        
        # Parse entry date
        entry_dt = pd.to_datetime(entry_date)
        
        # Fetch historical data (120 days to ensure we have data)
        hist = yf.download(
            normalized_ticker,
            start=entry_dt,
            end=entry_dt + timedelta(days=120),
            progress=False
        )["Close"]
        
        if hist.empty or len(hist) < 2:
            return {
                "status": "error",
                "message": f"Insufficient data for {ticker}",
                "ticker": ticker,
                "signal": signal,
            }
        
        # Use provided entry price or get from history
        if entry_price is None:
            entry_price = float(hist.iloc[0])
        else:
            # Adjust if provided price is very different
            if abs(entry_price - hist.iloc[0]) / hist.iloc[0] > 0.5:
                print(f"Warning: Provided entry price differs from historical")
        
        # Initialize tracking
        exit_price = float(hist.iloc[-1])  # Default to last price
        exit_date = hist.index[-1].strftime("%Y-%m-%d")
        days_held = len(hist) - 1
        
        # Check if target was hit
        if signal.upper() == "BUY":
            # For BUY signals, target is an upside target
            target_mask = hist >= target_price
        else:
            # For SELL signals, target is a downside target
            target_mask = hist <= target_price
        
        # Check if stop loss was hit (if specified)
        if stop_loss is not None:
            if signal.upper() == "BUY":
                # For BUY, stop loss is downside
                stop_mask = hist <= stop_loss
            else:
                # For SELL, stop loss is upside
                stop_mask = hist >= stop_loss
            
            # Find first occurrence (target vs stop)
            first_target = None
            first_stop = None
            
            if target_mask.any():
                first_target = target_mask.idxmax()
            if stop_mask.any():
                first_stop = stop_mask.idxmax()
            
            # Determine exit based on what hit first
            if first_target and first_stop:
                if first_target < first_stop:
                    exit_price = target_price
                    exit_date = first_target.strftime("%Y-%m-%d")
                    days_held = (first_target - hist.index[0]).days
                else:
                    exit_price = float(hist.loc[first_stop])
                    exit_date = first_stop.strftime("%Y-%m-%d")
                    days_held = (first_stop - hist.index[0]).days
            elif first_target:
                exit_price = target_price
                exit_date = first_target.strftime("%Y-%m-%d")
                days_held = (first_target - hist.index[0]).days
            elif first_stop:
                exit_price = float(hist.loc[first_stop])
                exit_date = first_stop.strftime("%Y-%m-%d")
                days_held = (first_stop - hist.index[0]).days
        else:
            # No stop loss, just check target
            if target_mask.any():
                first_idx = target_mask.idxmax()
                exit_price = target_price
                exit_date = first_idx.strftime("%Y-%m-%d")
                days_held = (first_idx - hist.index[0]).days
        
        # Calculate returns
        if signal.upper() == "BUY":
            profit = exit_price - entry_price
            return_pct = (profit / entry_price) * 100
        else:  # SELL
            profit = entry_price - exit_price
            return_pct = (profit / entry_price) * 100
        
        return {
            "status": "success",
            "ticker": ticker,
            "signal": signal,
            "entry_date": entry_date,
            "entry_price": round(entry_price, 2),
            "exit_date": exit_date,
            "exit_price": round(exit_price, 2),
            "target_price": round(target_price, 2),
            "stop_loss": round(stop_loss, 2) if stop_loss else None,
            "days_held": days_held,
            "profit_loss": round(profit, 2),
            "return_pct": round(return_pct, 2),
            "data_points": len(hist),
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "ticker": ticker,
            "signal": signal,
        }


def backtest_multiple_signals(signals: List[Dict]) -> List[Dict]:
    """
    Backtest multiple signals.
    
    Expected format for each signal:
    {
        "ticker": "AAPL",
        "signal": "BUY",
        "entry_date": "2024-01-01",
        "entry_price": 150.50,
        "target_price": 160.00,
        "stop_loss": 145.00
    }
    """
    results = []
    for sig in signals:
        result = backtest_signal(
            ticker=sig.get("ticker"),
            signal=sig.get("signal"),
            entry_date=sig.get("entry_date"),
            target_price=sig.get("target_price"),
            entry_price=sig.get("entry_price"),
            stop_loss=sig.get("stop_loss"),
        )
        results.append(result)
    
    return results


def calculate_win_rate(backtest_results: List[Dict]) -> Dict:
    """Calculate win rate statistics from backtest results"""
    if not backtest_results:
        return {"win_rate": 0, "total_trades": 0, "winners": 0, "losers": 0}
    
    successful_results = [r for r in backtest_results if r.get("status") == "success"]
    
    if not successful_results:
        return {"win_rate": 0, "total_trades": len(backtest_results), "winners": 0, "losers": 0}
    
    winners = [r for r in successful_results if r.get("return_pct", 0) > 0]
    losers = [r for r in successful_results if r.get("return_pct", 0) < 0]
    
    win_rate = (len(winners) / len(successful_results)) * 100 if successful_results else 0
    avg_profit = sum(r.get("return_pct", 0) for r in winners) / len(winners) if winners else 0
    avg_loss = sum(r.get("return_pct", 0) for r in losers) / len(losers) if losers else 0
    
    return {
        "win_rate": round(win_rate, 2),
        "total_trades": len(successful_results),
        "winners": len(winners),
        "losers": len(losers),
        "avg_profit_pct": round(avg_profit, 2),
        "avg_loss_pct": round(avg_loss, 2),
        "profit_factor": round(abs(avg_profit / avg_loss), 2) if avg_loss != 0 else 0,
    }
