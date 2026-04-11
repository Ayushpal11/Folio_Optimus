import SignalBadge from "./SignalBadge";
import { INDEX_PRESETS, swingSignal } from "../utils";

export default function SwingPanel({ batchData, selectedPreset, setSelectedPreset, onSelectSymbol, batchLoading }) {
  const screenerRows = batchData
    ? Object.keys(batchData.annualised_return).map((ticker) => {
        const ret = batchData.annualised_return[ticker];
        const vol = batchData.annualised_volatility[ticker];
        const sw = swingSignal(ret, vol, 100, 130, 70);
        return {
          ticker,
          ret,
          vol,
          sharpe: ret / (vol || 1),
          signal: sw?.signal || "HOLD",
          confidence: sw?.confidence || 50,
        };
      }).sort((a, b) => b.sharpe - a.sharpe)
    : [];

  return (
    <section className="swing-panel">
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

      <div className="card-grid">
        {screenerRows.map((row) => (
          <button key={row.ticker} type="button" className="swing-card" onClick={() => onSelectSymbol(row.ticker)}>
            <div className="swing-card-header">
              <div>
                <div className="swing-card-title">{row.ticker}</div>
                <div className="swing-card-sub">Ann. return {(row.ret * 100).toFixed(1)}%</div>
              </div>
              <SignalBadge signal={row.signal} />
            </div>
            <div className="swing-card-body">
              <div className="metric-pill">
                <span>Volatility</span>
                <strong>{(row.vol * 100).toFixed(1)}%</strong>
              </div>
              <div className="metric-pill">
                <span>Sharpe</span>
                <strong>{row.sharpe.toFixed(2)}</strong>
              </div>
              <div className="metric-pill">
                <span>Confidence</span>
                <strong>{row.confidence}%</strong>
              </div>
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}
