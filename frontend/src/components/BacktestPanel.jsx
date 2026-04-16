import React, { useState } from "react";
import "./BacktestPanel.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export default function BacktestPanel() {
  const [ticker, setTicker] = useState("AAPL");
  const [signal, setSignal] = useState("BUY");
  const [entryDate, setEntryDate] = useState("2024-01-01");
  const [entryPrice, setEntryPrice] = useState("");
  const [targetPrice, setTargetPrice] = useState("");
  const [stopLoss, setStopLoss] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);

  const handleBacktest = async () => {
    if (!ticker || !targetPrice) {
      setError("Please enter ticker and target price");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/backtest/${ticker.toUpperCase()}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          signal: signal.toUpperCase(),
          entry_date: entryDate,
          target_price: parseFloat(targetPrice),
          entry_price: entryPrice ? parseFloat(entryPrice) : undefined,
          stop_loss: stopLoss ? parseFloat(stopLoss) : undefined,
        }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Backtest failed");
      }

      const data = await response.json();
      setResult(data);

      // Add to history
      if (data.status === "success") {
        setHistory([data, ...history.slice(0, 9)]);
      }
    } catch (err) {
      setError(err.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    if (status === "success") return "#10b981";
    if (status === "error") return "#ef4444";
    return "#6b7280";
  };

  const getReturnColor = (returnPct) => {
    if (returnPct > 0) return "#10b981";
    if (returnPct < 0) return "#ef4444";
    return "#6b7280";
  };

  return (
    <div className="backtest-panel">
      <h2>Signal Backtester</h2>
      <p className="subtitle">Test historical trading signals</p>

      <div className="backtest-container">
        {/* Input Form */}
        <div className="backtest-form">
          <div className="form-row">
            <div className="form-group">
              <label>Ticker</label>
              <input
                type="text"
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                placeholder="e.g., AAPL"
                disabled={loading}
              />
            </div>
            <div className="form-group">
              <label>Signal</label>
              <select value={signal} onChange={(e) => setSignal(e.target.value)} disabled={loading}>
                <option value="BUY">BUY</option>
                <option value="SELL">SELL</option>
                <option value="HOLD">HOLD</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Entry Date</label>
              <input
                type="date"
                value={entryDate}
                onChange={(e) => setEntryDate(e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="form-group">
              <label>Entry Price (optional)</label>
              <input
                type="number"
                value={entryPrice}
                onChange={(e) => setEntryPrice(e.target.value)}
                placeholder="Auto-detect from market"
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Target Price</label>
              <input
                type="number"
                value={targetPrice}
                onChange={(e) => setTargetPrice(e.target.value)}
                placeholder="e.g., 160.00"
                disabled={loading}
              />
            </div>
            <div className="form-group">
              <label>Stop Loss (optional)</label>
              <input
                type="number"
                value={stopLoss}
                onChange={(e) => setStopLoss(e.target.value)}
                placeholder="e.g., 145.00"
                disabled={loading}
              />
            </div>
          </div>

          <button onClick={handleBacktest} disabled={loading} className="backtest-btn">
            {loading ? "Running Backtest..." : "Run Backtest"}
          </button>

          {error && <div className="error-message">{error}</div>}
        </div>

        {/* Result */}
        {result && result.status === "success" && (
          <div className="result-card">
            <div className="result-header">
              <div>
                <span className="result-ticker">{result.ticker}</span>
                <span className={`result-signal signal-${result.signal.toLowerCase()}`}>
                  {result.signal}
                </span>
              </div>
              <span
                className="result-return"
                style={{ color: getReturnColor(result.return_pct) }}
              >
                {result.return_pct > 0 ? "+" : ""}
                {result.return_pct}%
              </span>
            </div>

            <div className="result-grid">
              <div className="result-item">
                <span className="item-label">Entry</span>
                <span className="item-value">₹{result.entry_price.toLocaleString()}</span>
              </div>
              <div className="result-item">
                <span className="item-label">Exit</span>
                <span className="item-value">₹{result.exit_price.toLocaleString()}</span>
              </div>
              <div className="result-item">
                <span className="item-label">Days Held</span>
                <span className="item-value">{result.days_held}</span>
              </div>
              <div className="result-item">
                <span className="item-label">P&L</span>
                <span className="item-value" style={{ color: getReturnColor(result.profit_loss) }}>
                  ₹{result.profit_loss.toLocaleString()}
                </span>
              </div>
            </div>

            <div className="result-dates">
              <div>
                <strong>Entry:</strong> {result.entry_date}
              </div>
              <div>
                <strong>Exit:</strong> {result.exit_date}
              </div>
            </div>
          </div>
        )}

        {result && result.status === "error" && (
          <div className="error-card">
            <strong>Error:</strong> {result.message}
          </div>
        )}
      </div>

      {/* History Table */}
      {history.length > 0 && (
        <div className="history-section">
          <h3>Recent Backtests</h3>
          <table className="history-table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Signal</th>
                <th>Entry Price</th>
                <th>Exit Price</th>
                <th>Return %</th>
                <th>Days</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {history.map((item, idx) => (
                <tr key={idx}>
                  <td className="ticker-cell">{item.ticker}</td>
                  <td>
                    <span className={`signal-badge signal-${item.signal.toLowerCase()}`}>
                      {item.signal}
                    </span>
                  </td>
                  <td>₹{item.entry_price.toLocaleString()}</td>
                  <td>₹{item.exit_price.toLocaleString()}</td>
                  <td style={{ color: getReturnColor(item.return_pct) }}>
                    {item.return_pct > 0 ? "+" : ""}
                    {item.return_pct}%
                  </td>
                  <td>{item.days_held}</td>
                  <td>{item.entry_date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
