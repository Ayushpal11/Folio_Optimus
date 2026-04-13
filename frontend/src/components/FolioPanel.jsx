import { useState, useEffect } from "react";
import { fmt } from "../utils";

const HOLDING_POOL = [
  "RELIANCE",
  "TCS",
  "HDFC",
  "INFY",
  "ITC",
  "ICICIBANK",
  "LT",
  "HINDUNILVR",
  "ASIANPAINT",
  "BAJFINANCE",
  "TECHM",
  "SBIN",
  "AXISBANK",
  "MARUTI",
  "SUNPHARMA",
  "BHARTIARTL",
  "NESTLEIND",
  "TITAN",
  "WIPRO",
  "HCLTECH",
  "ONGC",
  "ADANIENT",
  "ULTRACEMCO",
  "JSWSTEEL",
  "CIPLA",
  "JSWENERGY",
  "DRREDDY",
  "M&M",
  "TATAMOTORS",
  "HDFCAMC",
];

const randomSampleHoldings = (count = 12) => {
  const shuffled = [...HOLDING_POOL].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, count).map((ticker) => ({
    ticker,
    qty: Math.floor(Math.random() * 90) + 10,
    avg_price: Number((Math.random() * 450 + 50).toFixed(2)),
    exchange: Math.random() > 0.2 ? "NSE" : "BSE",
  }));
};

export default function FolioPanel() {
  const [rows, setRows] = useState(() => randomSampleHoldings());
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const updateRow = (index, field, value) => {
    setRows((current) => current.map((row, idx) => (idx === index ? { ...row, [field]: value } : row)));
  };

  const addRow = () => setRows((current) => [...current, { ticker: "", qty: 0, avg_price: 0, exchange: "NSE" }]);
  const removeRow = (index) => setRows((current) => current.filter((_, idx) => idx !== index));
  useEffect(() => {
    const loadHiddenHoldings = async () => {
      try {
        const res = await fetch("/.default_holdings_hidden.json");
        if (!res.ok) return;
        const holdings = await res.json();
        if (Array.isArray(holdings) && holdings.length) {
          setRows(holdings);
        }
      } catch (error) {
        // Hidden override not present locally.
      }
    };

    loadHiddenHoldings();
  }, []);

  const loadDefaultHoldings = () => setRows(randomSampleHoldings());

  const analyze = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const payload = { holdings: rows.map((row) => ({ ...row, ticker: row.ticker.trim() })) };
      const res = await fetch(`/api/folio/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Unable to analyze folio.");
      setResult(data);
    } catch (err) {
      setError(err.message || "Analysis failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="folio-panel card">
      <div className="preset-row" style={{ justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
        <div>
          <h2 style={{ margin: 0 }}>Folio Analyzer</h2>
          <p className="panel-description">
            Enter your holdings and buy price. Stock names or tickers are accepted.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button type="button" className="button secondary" onClick={loadDefaultHoldings} disabled={loading}>
            Load sample portfolio
          </button>
          <button type="button" className="button primary" onClick={analyze} disabled={loading}>
            {loading ? "Analyzing..." : "Analyze My Folio"}
          </button>
        </div>
      </div>

      <div className="table-card" style={{ marginTop: 18 }}>
        <div className="section-heading">Holdings</div>
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Stock</th>
                <th>Qty</th>
                <th>Avg Price</th>
                <th>Exchange</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={index}>
                  <td>
                    <input
                      value={row.ticker}
                      onChange={(e) => updateRow(index, "ticker", e.target.value)}
                      className="search-input"
                      placeholder="RELIANCE, TCS, AAPL"
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      value={row.qty}
                      onChange={(e) => updateRow(index, "qty", Number(e.target.value))}
                      className="search-input"
                      min="0"
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      value={row.avg_price}
                      onChange={(e) => updateRow(index, "avg_price", Number(e.target.value))}
                      className="search-input"
                      min="0"
                      step="0.01"
                    />
                  </td>
                  <td>
                    <select
                      value={row.exchange}
                      onChange={(e) => updateRow(index, "exchange", e.target.value)}
                      className="search-input"
                    >
                      <option>NSE</option>
                      <option>BSE</option>
                      <option>US</option>
                    </select>
                  </td>
                  <td>
                    <button type="button" className="button secondary" onClick={() => removeRow(index)}>
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <button type="button" className="button pill" onClick={addRow} style={{ marginTop: 14 }}>
          Add Holding
        </button>
      </div>

      {error && <div className="alert error" style={{ marginTop: 16 }}>{error}</div>}

      {result && (
        <div className="dashboard-panel" style={{ marginTop: 20 }}>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">Total Invested</div>
              <div className="stat-value">{fmt(result.summary.total_invested)}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Current Value</div>
              <div className="stat-value">{fmt(result.summary.total_current)}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Total P&L</div>
              <div className="stat-value">{fmt(result.summary.total_pnl)}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Return</div>
              <div className="stat-value">{result.summary.total_pnl_pct.toFixed(2)}%</div>
            </div>
          </div>

          <div className="portfolio-status-card" style={{ marginTop: 20, padding: 16, border: '1px solid var(--border)', borderRadius: 8 }}>
            <h3>Portfolio Status</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span className={`signal-badge ${result.summary.portfolio_status.toLowerCase()}`}>
                {result.summary.portfolio_status}
              </span>
              <p style={{ margin: 0 }}>{result.summary.portfolio_reason}</p>
            </div>
          </div>

          <div className="table-card" style={{ marginTop: 18 }}>
            <div className="section-heading">Per-stock Guidance</div>
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Ticker</th>
                    <th>Name</th>
                    <th>Action</th>
                    <th>P&L</th>
                    <th>Stop Loss</th>
                    <th>Target</th>
                    <th>Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {result.holdings.map((item, index) => (
                    <tr key={`${item.ticker}-${index}`}>
                      <td>{item.ticker}</td>
                      <td>{item.name}</td>
                      <td>
                        <span
                          className={`signal-badge ${item.signal.toLowerCase().replace(/ /g, "-")}`}
                        >
                          {item.signal}
                        </span>
                      </td>
                      <td className={item.pnl >= 0 ? "positive" : "negative"}>
                        {item.pnl >= 0 ? "+" : ""}
                        {fmt(item.pnl)} ({item.pnl_pct}%)
                      </td>
                      <td>{fmt(item.stop_loss)}</td>
                      <td>{fmt(item.target)}</td>
                      <td>{item.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
