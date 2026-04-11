export default function SearchPanel({
  ticker,
  setTicker,
  lookupStock,
  loading,
  error,
  presetSymbols,
  onPresetClick,
}) {
  return (
    <section className="search-panel">
      <div className="search-row">
        <input
          className="search-input"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && lookupStock()}
          placeholder="RELIANCE.NS · TCS.NS · AAPL · INFY.NS"
        />
        <button className="button primary" onClick={() => lookupStock()} disabled={loading}>
          {loading ? "Loading..." : "Analyse"}
        </button>
      </div>

      <div className="preset-group">
        {presetSymbols.map((symbol) => (
          <button key={symbol} type="button" className="button pill" onClick={() => onPresetClick(symbol)}>
            {symbol.replace(".NS", "")}
          </button>
        ))}
      </div>

      {error && <div className="alert error">{error}</div>}
    </section>
  );
}
