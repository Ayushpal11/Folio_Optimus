import { ResponsiveContainer, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Bar } from "recharts";
import SignalBadge from "./SignalBadge";
import { INDEX_PRESETS } from "../utils";

export default function ScreenerPanel({ batchData, selectedPreset, setSelectedPreset, batchLoading, onSelectSymbol, onPresetToggle }) {
  const screenerRows = batchData
    ? Object.keys(batchData.annualised_return).map((ticker) => {
        const ret = batchData.annualised_return[ticker];
        const vol = batchData.annualised_volatility[ticker];
        const sharpe = ret / (vol || 1);
        const signal = ret > 0.05 ? "BUY" : ret < -0.02 ? "SELL" : "HOLD";
        const confidence = Math.round(Math.min(90, Math.abs(ret) * 200));
        return { ticker, ret, vol, sharpe, signal, confidence };
      }).sort((a, b) => b.sharpe - a.sharpe)
    : [];

  return (
    <section className="screener-panel">
      <div className="preset-row">
        {Object.keys(INDEX_PRESETS).map((preset) => (
          <button
            key={preset}
            type="button"
            className={`button pill ${selectedPreset === preset ? "active" : ""}`}
            onClick={() => setSelectedPreset(preset)}
          >
            {preset}
          </button>
        ))}
        {batchLoading && <span className="text-muted">Fetching data...</span>}
      </div>

      {batchData && (
        <>
          <div className="chart-card">
            <div className="section-heading">Return vs Volatility — {selectedPreset}</div>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={screenerRows.slice(0, 10)} margin={{ top: 8, right: 16, left: 0, bottom: 28 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis dataKey="ticker" tick={{ fill: "var(--muted)", fontSize: 10 }} angle={-30} textAnchor="end" />
                <YAxis tick={{ fill: "var(--muted)", fontSize: 10 }} tickFormatter={(value) => `${(value * 100).toFixed(0)}%`} />
                <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border-color)", borderRadius: 12, color: "var(--text)" }} formatter={(value) => [`${(value * 100).toFixed(1)}%`]} />
                <Legend wrapperStyle={{ fontSize: 11, color: "var(--muted)" }} />
                <Bar dataKey="ret" name="Ann. Return" fill="var(--accent)" radius={[6, 6, 0, 0]} />
                <Bar dataKey="vol" name="Volatility" fill="var(--danger)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-card">
            <div className="section-heading">Sharpe Ratio Ranking</div>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={screenerRows.slice(0, 10)} layout="vertical" margin={{ top: 8, right: 34, left: 80, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" horizontal={false} />
                <XAxis type="number" tick={{ fill: "var(--muted)", fontSize: 10 }} tickFormatter={(value) => value.toFixed(2)} />
                <YAxis type="category" dataKey="ticker" tick={{ fill: "var(--muted)", fontSize: 10 }} width={84} />
                <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border-color)", borderRadius: 12, color: "var(--text)" }} formatter={(value) => [value.toFixed(3), "Sharpe"]} />
                <Bar dataKey="sharpe" name="Sharpe Ratio" fill="var(--secondary)" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="table-card">
            <div className="section-heading">Stock Screener — {selectedPreset}</div>
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Ticker</th>
                    <th>Ann. Return</th>
                    <th>Volatility</th>
                    <th>Sharpe</th>
                    <th>Signal</th>
                    <th>Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {screenerRows.map((row, index) => (
                    <tr key={row.ticker} className="table-row" onClick={() => onSelectSymbol(row.ticker)}>
                      <td>
                        <span className={index < 3 ? "top-ticker" : undefined}>
                          {index < 3 ? "★ " : ""}{row.ticker}
                        </span>
                      </td>
                      <td className={row.ret > 0 ? "positive" : "negative"}>{row.ret > 0 ? "+" : ""}{(row.ret * 100).toFixed(1)}%</td>
                      <td>{(row.vol * 100).toFixed(1)}%</td>
                      <td className={row.sharpe > 1 ? "positive" : row.sharpe > 0.5 ? "neutral" : "muted"}>{row.sharpe.toFixed(2)}</td>
                      <td><SignalBadge signal={row.signal} /></td>
                      <td>
                        <div className="confidence-bar">
                          <div className="confidence-fill" style={{ width: `${row.confidence}%`, backgroundColor: row.signal === "BUY" ? "var(--accent)" : row.signal === "SELL" ? "var(--danger)" : "var(--warning)" }} />
                        </div>
                        <span className="confidence-label">{row.confidence}%</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
