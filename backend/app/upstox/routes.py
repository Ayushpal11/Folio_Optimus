import os
from fastapi import APIRouter, HTTPException
from app.upstox.client import UpstoxClient
from app.utils.ticker_mapper import get_instrument_key

router = APIRouter()

ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")


def get_client() -> UpstoxClient:
    if not ACCESS_TOKEN:
        raise EnvironmentError("UPSTOX_ACCESS_TOKEN is not configured")
    return UpstoxClient(ACCESS_TOKEN)


@router.get("/ltp/{symbol}")
def get_ltp(symbol: str):
    instrument = get_instrument_key(symbol)
    if not instrument:
        raise HTTPException(status_code=404, detail=f"No instrument mapping found for symbol: {symbol}")

    try:
        client = get_client()
        data = client.get_ltp(instrument)
        return {"symbol": symbol, "instrument_key": instrument, "ltp": data.get("data", data)}
    except EnvironmentError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstox LTP request failed: {str(e)}")


@router.get("/history/{symbol}")
def get_history(symbol: str, interval: str = "day", from_date: str = None, to_date: str = None):
    instrument = get_instrument_key(symbol)
    if not instrument:
        raise HTTPException(status_code=404, detail=f"No instrument mapping found for symbol: {symbol}")

    try:
        client = get_client()
        data = client.get_historical(instrument, interval=interval, from_date=from_date, to_date=to_date)
        return {"symbol": symbol, "instrument_key": instrument, "interval": interval, "data": data}
    except EnvironmentError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstox history request failed: {str(e)}")
