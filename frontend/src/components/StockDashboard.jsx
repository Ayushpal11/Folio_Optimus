import { ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis } from "recharts";
import StatCard from "./StatCard";
import SignalBadge from "./SignalBadge";
import PriceSparkline from "./PriceSparkline";
import { fmt, fmtMktCap } from "../utils";

export default function StockDashboard({ stockData, priceHistory, sw, radarData, onSwitchExchange }) {
  if (!stockData) return null;
  const switchable = stockData.ticker?.endsWith(".NS") || stockData.ticker?.endsWith(".BO");
  const otherTicker = stockData.ticker?.endsWith(".NS")
    ? stockData.ticker.replace(/\.NS$/, ".BO")
    : stockData.ticker?.endsWith(".BO")
    ? stockData.ticker.replace(/\.BO$/, ".NS")
    : null;
  const rangePct = stockData["52w_high"] && stockData["52w_low"]
    ? Math.round(((stockData.current_price - stockData["52w_low"]) / ((stockData["52w_high"] - stockData["52w_low"]) || 1)) * 100)
    : 0;

  return (
    <section className="dashboard-panel">
      {switchable && otherTicker && (
        <div className="exchange-toggle-row">
          <button
            type="button"
            className="button secondary"
            onClick={() => onSwitchExchange(otherTicker)}
          >
            Switch to {otherTicker.endsWith(".NS") ? "NSE" : "BSE"} ({otherTicker})
          </button>
        </div>
      )}
      <div className="stats-grid">
        <StatCard
          label="Current Price"
          value={stockData.currency === "INR" ? `₹${stockData.current_price?.toLocaleString("en-IN")}` : `$${stockData.current_price}`}
          sub={stockData.name}
        />
        <StatCard
          label="Ann. Return"
          value={`${(stockData.annualised_return * 100).toFixed(1)}%`}
          sub="1-year annualised"
        />
        <StatCard
          label="Volatility"
          value={`${(stockData.annualised_volatility * 100).toFixed(1)}%`}
          sub="Annualised σ"
        />
        <StatCard
          label="P/E Ratio"
          value={stockData.pe_ratio ? fmt(stockData.pe_ratio) : "—"}
          sub="Trailing"
        />
        <StatCard
          label="Market Cap"
          value={fmtMktCap(stockData.market_cap, stockData.currency)}
          sub={stockData.sector}
        />
        {sw && (
          <StatCard
            label="Swing Signal"
            value={sw.signal}
            sub={`${sw.confidence}% confidence`}
          />
        )}
      </div>

      <div className="charts-grid">
        <div className="card range-card">
          <div className="section-heading">52-Week Range</div>
          <div className="range-row">
            <span>{stockData["52w_low"] ? `₹${stockData["52w_low"].toLocaleString("en-IN")}` : "—"}</span>
            <div className="range-bar-container">
              <div className="range-bar-fill" style={{ width: `${rangePct}%` }} />
              <div className="range-pointer" style={{ left: `calc(${rangePct}% - 7px)` }} />
            </div>
            <span>{stockData["52w_high"] ? `₹${stockData["52w_high"].toLocaleString("en-IN")}` : "—"}</span>
          </div>
          <div className="range-summary">
            Current: {stockData.currency === "INR" ? "₹" : "$"}{stockData.current_price?.toLocaleString("en-IN")} · {rangePct}% from low
          </div>

          <div className="sparkline-block">
            <div className="section-subtitle">Price History</div>
            <PriceSparkline history={priceHistory} />
          </div>

          {sw && (
            <div className="swing-metrics">
              <div className="swing-card">
                <div className="card-label">STOP LOSS</div>
                <div className="card-value">{stockData.currency === "INR" ? `₹${sw.stopLoss.toLocaleString("en-IN")}` : `$${sw.stopLoss}`}</div>
              </div>
              <div className="swing-card">
                <div className="card-label">TARGET</div>
                <div className="card-value">{stockData.currency === "INR" ? `₹${sw.target.toLocaleString("en-IN")}` : `$${sw.target}`}</div>
              </div>
              <div className="swing-card">
                <div className="card-label">SIGNAL</div>
                <SignalBadge signal={sw.signal} />
              </div>
            </div>
          )}
        </div>

        <div className="card profile-card">
          <div className="section-heading">Stock Profile</div>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="var(--border-color)" />
              <PolarAngleAxis dataKey="metric" tick={{ fill: "var(--muted)", fontSize: 11 }} />
              <Radar dataKey="value" stroke="var(--accent)" fill="var(--accent)" fillOpacity={0.25} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
          <div className="profile-meta">{stockData.industry} · {stockData.sector}</div>
        </div>
      </div>
    </section>
  );
}
