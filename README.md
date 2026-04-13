# Portfolio Optimizer

A comprehensive full-stack portfolio optimization tool with real-time stock analysis, screener, swing signals, SIP calculator, and portfolio analyzer. Features a responsive React frontend with dark/light theme support and a FastAPI backend powered by yfinance data.

## 🚀 Live Deployments
- **Frontend**: [https://folio-optimus.vercel.app](https://folio-optimus.vercel.app)
- **Backend API**: [https://folio-optimus.onrender.com](https://folio-optimus.onrender.com)

## ✨ Features
- **Stock Dashboard**: Real-time stock analysis with price charts, 52-week range, P/E ratio, market cap, and volatility metrics
- **Stock Screener**: Compare multiple stocks with return/volatility charts, Sharpe ratios, and ranking tables
- **Swing Signals**: AI-powered buy/sell/hold signals with confidence scores and stop-loss targets
- **Folio Analyzer**: Analyze your existing portfolio holdings with per-stock guidance (buy/sell/hold) and overall portfolio health assessment
- **SIP Calculator**: Interactive systematic investment plan calculator with growth projections
- **Stock Search**: Fuzzy search by ticker or company name with autocomplete suggestions
- **Upstox Integration**: Real-time LTP (Last Trading Price) and historical data for Indian stocks via Upstox API
- **Multi-Exchange Support**: Support for NSE and BSE stocks with unified interface
- **Responsive Design**: Optimized for mobile, tablet, and desktop devices
- **Dark/Light Theme**: Automatic theme detection with manual toggle
- **Real-time Data**: Live stock prices and historical data via yfinance and Upstox

## 🛠 Tech Stack
- **Backend**: FastAPI, Python, yfinance, NumPy, Pandas, PyPortfolioOpt, Upstox API
- **Frontend**: React, Vite, Recharts, CSS Variables
- **Deployment**: Render (Backend), Vercel (Frontend)
- **Data Sources**: Yahoo Finance (yfinance library), Upstox API (Indian stocks)
- **Features**: Fuzzy search, portfolio analysis, responsive design, dark/light themes, real-time market data

## 📁 Project Structure
```
Portfolio_Optimizer/
├── README.md
├── backend/
│   ├── .env
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py          # FastAPI app with CORS, endpoints
│   └── data/
│       ├── __init__.py
│       └── fetcher.py        # yfinance data fetching and processing
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx           # Main app shell with theme/state management
│       ├── main.jsx          # React entry point
│       ├── style.css         # Global styles with theme variables
│       ├── utils.js          # API URLs, formatters, swing logic
│       └── components/       # Reusable UI components
│           ├── TopBar.jsx    # Header with branding and theme toggle
│           ├── TabBar.jsx    # Navigation tabs
│           ├── SearchPanel.jsx # Stock search with autocomplete
│           ├── StockDashboard.jsx # Stock analysis cards and charts
│           ├── ScreenerPanel.jsx # Multi-stock comparison
│           ├── SwingPanel.jsx # Swing signal cards
│           ├── FolioPanel.jsx # Portfolio holdings analyzer
│           ├── SIPCalc.jsx    # SIP calculator with charts
│           ├── StatCard.jsx   # Metric display cards
│           ├── PriceSparkline.jsx # Price history sparkline
│           └── SignalBadge.jsx # Buy/Sell/Hold badges
```

## 🏗 Current Status
- ✅ **Backend Complete**: FastAPI server with all endpoints deployed on Render
  - `/` - Health check
  - `/api/search` - Fuzzy stock search by name or ticker
  - `/api/stock/{ticker}` - Single stock metadata and stats
  - `/api/price-history/{ticker}` - Historical price data
  - `/api/analyst/{ticker}` - Analyst recommendations and data
  - `/api/batch-stats` - Multi-stock analysis
  - `/api/folio/analyze` - Portfolio holdings analysis with per-stock guidance
  - `/api/optimize` - Portfolio optimization (stub for future AI integration)
  - `/api/upstox/ltp/{symbol}` - Real-time LTP data for Indian stocks via Upstox
  - `/api/upstox/history/{symbol}` - Historical OHLC data via Upstox API
- ✅ **Frontend Complete**: Fully responsive React app deployed on Vercel
  - Component-based architecture for maintainability
  - Dark/light theme with CSS variables
  - Mobile-first responsive design
  - Interactive charts with Recharts
  - Stock search with autocomplete
  - Portfolio analyzer with holdings input and guidance
- ✅ **Deployment**: Both backend and frontend deployed and working
- ✅ **Data Integration**: Real-time stock data via yfinance and Upstox API
- ✅ **Upstox Integration**: Live Indian stock data with LTP and historical support
- 🔄 **Future Plans**: Enhanced Upstox integration, AI-powered portfolio optimization, user accounts, watchlists

## 🚀 Setup & Development

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### Backend Setup
1. Clone the repository and navigate to backend
   ```bash
   cd backend
   ```

2. Create virtual environment
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Run the development server
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```

### Frontend Setup
1. Navigate to frontend directory
   ```bash
   cd frontend
   ```

2. Install dependencies
   ```bash
   npm install
   ```

3. Start development server
   ```bash
   npm run dev
   ```

4. Open [http://localhost:5173](http://localhost:5173) in your browser

## 📖 Usage
1. **Stock Analysis**: Enter a ticker (e.g., `AAPL`, `RELIANCE.NS`) or search by company name in the search bar
2. **Screener**: Select preset indices to compare multiple stocks
3. **Swing Signals**: View AI-generated trading signals with confidence levels
4. **Folio Analyzer**: Input your stock holdings with quantities and purchase prices to get per-stock buy/sell/hold guidance and overall portfolio health assessment
5. **SIP Calculator**: Calculate potential returns from systematic investments
6. **Theme Toggle**: Switch between dark and light modes

### API Endpoints
- `GET /api/search?q={query}` - Fuzzy search stocks by name or ticker
- `GET /api/stock/{ticker}` - Get stock information
- `GET /api/price-history/{ticker}` - Get price history
- `GET /api/analyst/{ticker}` - Get analyst recommendations
- `POST /api/batch-stats` - Analyze multiple stocks
- `GET /api/upstox/ltp/{symbol}` - Get real-time LTP for Indian stocks
- `GET /api/upstox/history/{symbol}?interval={interval}&from_date={date}&to_date={date}` - Get historical data from Upstox
- `POST /api/folio/analyze` - Analyze portfolio holdings
- `POST /api/optimize` - Portfolio optimization (coming soon)

## � AI Advisor (4-Layer Signal Stack)

The AI Advisor uses a sophisticated 4-layer intelligence system to recommend stocks:

### 📊 Scoring Layers

**📰 News Sentiment (35%)**
- Real-time news analysis using Marketaux API
- Fallback to local FinBERT model for financial text sentiment
- Detects bullish/bearish sentiment from recent news

**📈 Macro Trend (25%)**
- Sector index performance vs 50-day moving average
- Macro theme detection (Defence, EV, Infra, AI, Pharma, etc.)
- Outperformance vs Nifty 50 benchmark

**🏢 Fundamental Health (25%)**
- Debt-to-equity ratios
- Revenue and earnings growth
- Promoter/insider holdings
- Market capitalization stability

**⚡ Technical Momentum (15%)**
- Volume spikes and accumulation patterns
- Price position relative to 52-week highs
- Short-term momentum (20-day returns)
- RSI and technical indicators

### 🎯 How It Works

1. **Dynamic Universe**: Fetches live stock lists from NSE indices (50-500 stocks)
2. **Multi-Layer Scoring**: Each stock scored across all 4 intelligence layers
3. **Risk-Adjusted**: Safe/Moderate/Aggressive profiles filter and weight scores
4. **Sector Focus**: Optional sector filtering using NSE classifications
5. **Top Picks**: Returns 8 best-scoring stocks with signals and targets

### 🔧 Setup (Optional APIs)

For enhanced news sentiment, add API keys to `backend/.env`:

```bash
# Marketaux (recommended) - 100 requests/day free
MARKETAUX_API_KEY=your_key_here

# Alpha Vantage (fallback) - 25 requests/day free  
ALPHA_VANTAGE_API_KEY=your_key_here
```

Without API keys, the system uses local FinBERT model for sentiment analysis.

## 📄 License
This project is open source and available under the [MIT License](LICENSE).

## 📞 Support
For questions or issues, please open a GitHub issue or contact the maintainers.
