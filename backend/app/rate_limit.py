from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)


async def rate_limit_error_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit error handler"""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded",
            "retry_after": exc.retry_after if hasattr(exc, 'retry_after') else 60
        },
    )


# Rate limiting rules (format: "requests/period")
RATE_LIMITS = {
    "search": "100/minute",           # /api/search
    "stock": "50/minute",              # /api/stock
    "batch": "20/minute",              # /api/batch-stats
    "optimize": "10/minute",           # /api/optimize - heavy operation
    "recommend": "10/minute",          # /api/recommend - heavy operation
    "auth": "5/minute",                # /auth/* - authentication endpoints
    "backtest": "10/minute",           # /api/backtest
}
