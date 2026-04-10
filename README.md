# Portfolio Optimizer

A full-stack portfolio optimizer with a React frontend and FastAPI backend.

## Current Status
- Backend data module created in `backend/data/fetcher.py`.
- `GET /api/stock/{ticker}` returns stock metadata plus 1Y annualised stats.
- `POST /api/batch-stats` returns returns matrix, correlation matrix, and batch stats for ticker lists.
- Cached yfinance results using `cachetools` to reduce repeated fetches.
- Frontend currently supports a stock lookup panel in `frontend/src/App.jsx` for Phase 2 validation.
- The optimization endpoint is still a stub/mocked response and will be replaced by Phase 3 optimization logic.

## Project Structure
```text
backend/
  .env
  requirements.txt
  app/
    __init__.py
    main.py
  data/
    __init__.py
    fetcher.py
frontend/
  index.html
  package.json
  vite.config.js
  src/
    App.jsx
    main.jsx
    style.css
```

## Setup

### Backend
1. Create a Python virtual environment
   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. Run the backend
   ```powershell
   cd backend
   python -m uvicorn app.main:app --reload --port 8000
   ```

### Frontend
1. Install dependencies
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```
2. Open the URL shown by Vite (usually `http://localhost:5173`).

## Usage
- Use the frontend stock lookup panel to test data retrieval.
- Enter a ticker like `AAPL`, `RELIANCE.NS`, or `RELIANCE.BO`.
- Verify metadata and annualised stats load successfully.

## Notes
- Indian NSE tickers require `.NS` suffix (e.g. `RELIANCE.NS`).
- Indian BSE tickers require `.BO` suffix (e.g. `RELIANCE.BO`).
- The backend cache TTL is configurable in `backend/.env` using `YFINANCE_CACHE_TTL`.
- Phase 3 will wire the fetcher into the portfolio optimizer math engine.
