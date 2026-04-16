import React, { useState, useMemo, useRef, useEffect } from "react";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { API } from "../utils";
import "./FolioOptimizer.css";

const API_BASE = API;

export default function FolioOptimizer() {
  const [tickerInput, setTickerInput] = useState("");
  const [tickerList, setTickerList] = useState(["AAPL", "MSFT", "GOOGL"]);
  const [capital, setCapital] = useState(100000);
  const [riskTolerance, setRiskTolerance] = useState("medium");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [open, setOpen] = useState(false);
  const [searching, setSearching] = useState(false);
  const debounceRef = useRef(null);
  const containerRef = useRef(null);

  const tickerArray = useMemo(() => tickerList, [tickerList]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const fetchSuggestions = async (text) => {
    if (!text.trim()) {
      setSuggestions([]);
      setOpen(false);
      return;
    }

    setSearching(true);
    try {
      const response = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(text)}`);
      const data = await response.json();
      setSuggestions(data.results || []);
      setOpen(true);
    } catch (err) {
      setSuggestions([]);
    } finally {
      setSearching(false);
    }
  };

  const onSearchChange = (value) => {
    setTickerInput(value);
    setError(null);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchSuggestions(value), 250);
  };

  const chooseSuggestion = (symbol) => {
    if (symbol && !tickerList.includes(symbol)) {
      setTickerList((prev) => [...prev, symbol]);
    }
    setTickerInput("");
    setSuggestions([]);
    setOpen(false);
  };

  const addTicker = () => {
    const newTickers = tickerInput
      .split(",")
      .map((t) => t.trim().toUpperCase())
      .filter((t) => t && !tickerList.includes(t));

    if (newTickers.length === 0) {
      setError("Enter a valid new ticker to add.");
      return;
    }

    setTickerList((prev) => [...prev, ...newTickers]);
    setTickerInput("");
    setSuggestions([]);
    setOpen(false);
    setError(null);
  };

  const removeTicker = (ticker) => {
    setTickerList((prev) => prev.filter((t) => t !== ticker));
    setError(null);
  };

  const handleOptimize = async () => {
    if (tickerArray.length === 0) {
      setError("Please add at least one ticker.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/optimize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tickers: tickerArray,
          capital: parseFloat(capital),
          risk_tolerance: riskTolerance,
        }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Optimization failed");
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  // Prepare pie chart data from weights
  const pieData = useMemo(() => {
    if (!result) return [];
    return Object.entries(result.weights)
      .filter(([, weight]) => weight > 0.001) // Only show non-trivial weights
      .map(([ticker, weight]) => ({
        name: ticker,
        value: parseFloat((weight * 100).toFixed(2)),
      }));
  }, [result]);

  const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"];

  // Risk badge colors
  const getRiskColor = (risk) => {
    if (risk === "low") return "#10b981";
    if (risk === "high") return "#ef4444";
    return "#f59e0b";
  };

  return (
    <div className="folio-optimizer">
      <h2>Portfolio Optimizer</h2>
      <p className="subtitle">Markowitz Efficient Frontier Optimization</p>

      <div className="optimizer-container">
        {/* Left: Input Panel */}
        <div className="input-panel">
          <div className="form-group" ref={containerRef}>
            <label>Tickers</label>
            <div className="ticker-input-row">
              <input
                type="text"
                value={tickerInput}
                onChange={(e) => onSearchChange(e.target.value)}
                placeholder="Search by name or ticker — e.g. AAPL, Reliance"
                className="search-input"
                disabled={loading}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addTicker();
                  }
                }}
              />
              <button
                type="button"
                className="secondary-btn"
                onClick={addTicker}
                disabled={loading || !tickerInput.trim()}
              >
                Add Stock
              </button>
            </div>

            {open && suggestions.length > 0 && (
              <div className="search-suggestions">
                {suggestions.map((item) => (
                  <button
                    key={`${item.ticker}-${item.exchange}`}
                    type="button"
                    className="suggestion-item"
                    onClick={() => chooseSuggestion(item.ticker)}
                  >
                    <div>{item.name}</div>
                    <div className="suggestion-meta">
                      {item.ticker} · {item.exchange}
                    </div>
                  </button>
                ))}
              </div>
            )}

            <div className="ticker-tags">
              {tickerList.map((ticker) => (
                <span key={ticker} className="ticker-tag">
                  {ticker}
                  <button
                    type="button"
                    className="ticker-remove"
                    onClick={() => removeTicker(ticker)}
                    disabled={loading}
                    aria-label={`Remove ${ticker}`}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
            <small>{tickerArray.length} ticker(s) entered</small>
            {searching && <div className="alert info">Searching...</div>}
          </div>

          <div className="form-group">
            <label>Total Capital (₹)</label>
            <input
              type="number"
              value={capital}
              onChange={(e) => setCapital(e.target.value)}
              placeholder="100000"
              className="input-field"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label>Risk Tolerance</label>
            <select
              value={riskTolerance}
              onChange={(e) => setRiskTolerance(e.target.value)}
              className="input-field"
              disabled={loading}
            >
              <option value="low">Low (Min Volatility)</option>
              <option value="medium">Medium (Max Sharpe)</option>
              <option value="high">High (Max Return)</option>
            </select>
          </div>

          <button
            onClick={handleOptimize}
            disabled={loading}
            className={`optimize-btn ${loading ? "loading" : ""}`}
          >
            {loading ? "Optimizing..." : "Optimize Portfolio"}
          </button>

          {error && <div className="error-message">{error}</div>}
        </div>

        {/* Right: Results */}
        {result && (
          <div className="results-panel">
            <div className="metrics-grid">
              <div className="metric-card">
                <span className="metric-label">Expected Return</span>
                <span className="metric-value">
                  {(result.performance.expected_annual_return * 100).toFixed(2)}%
                </span>
              </div>
              <div className="metric-card">
                <span className="metric-label">Annual Volatility</span>
                <span className="metric-value">
                  {(result.performance.annual_volatility * 100).toFixed(2)}%
                </span>
              </div>
              <div className="metric-card">
                <span className="metric-label">Sharpe Ratio</span>
                <span className="metric-value">{result.performance.sharpe_ratio.toFixed(2)}</span>
              </div>
              <div className="metric-card">
                <span className="metric-label">Risk Profile</span>
                <span
                  className="metric-badge"
                  style={{ backgroundColor: getRiskColor(result.risk_tolerance) }}
                >
                  {result.risk_tolerance.toUpperCase()}
                </span>
              </div>
            </div>

            <div className="allocation-cash">
              <div>
                <strong>Allocated:</strong> ₹{result.total_allocated.toLocaleString()}
              </div>
              <div>
                <strong>Leftover Cash:</strong> ₹{result.leftover_cash.toLocaleString()}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Visualization: Pie + Table */}
      {result && (
        <div className="visualization-section">
          {pieData.length > 0 && (
            <div className="chart-container">
              <h3>Portfolio Allocation</h3>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name} ${value}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          <div className="allocation-table">
            <h3>Share Allocation</h3>
            <table>
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Shares</th>
                  <th>Price (₹)</th>
                  <th>Investment (₹)</th>
                  <th>Weight %</th>
                </tr>
              </thead>
              <tbody>
                {result.allocation.map((item, idx) => (
                  <tr key={idx}>
                    <td className="ticker-cell">{item.ticker}</td>
                    <td>{item.shares}</td>
                    <td>₹{item.price.toLocaleString()}</td>
                    <td>₹{item.value.toLocaleString()}</td>
                    <td>{item.weight}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!result && !error && (
        <div className="empty-state">
          <p>Enter tickers and click "Optimize Portfolio" to start</p>
        </div>
      )}
    </div>
  );
}
