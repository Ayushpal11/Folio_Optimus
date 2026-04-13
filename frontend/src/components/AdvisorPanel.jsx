import { useState, useEffect, useMemo } from "react";
import { API } from "../utils";
import "./AdvisorPanel.css";

const SECTORS = [
  "All",
  "IT",
  "Banking",
  "Pharma",
  "Automotive",
  "Energy",
  "Healthcare",
  "Retail",
];

const DURATIONS = [
  { id: "short", label: "Short (1-3 months)", icon: "⚡" },
  { id: "mid", label: "Medium (3-9 months)", icon: "📊" },
  { id: "long", label: "Long (1+ years)", icon: "🌱" },
];

const RISK_LEVELS = [
  {
    id: "safe",
    label: "Safe",
    desc: "Large cap, Low volatility",
    icon: "🛡️",
    color: "#4ade80",
  },
  {
    id: "moderate",
    label: "Moderate",
    desc: "Mid cap, Balanced growth",
    icon: "⚖️",
    color: "#facc15",
  },
  {
    id: "aggressive",
    label: "Aggressive",
    desc: "High beta, High returns",
    icon: "🔥",
    color: "#f87171",
  },
];

export default function AdvisorPanel({ onSelectSymbol }) {
  const [risk, setRisk] = useState("moderate");
  const [duration, setDuration] = useState("mid");
  const [sector, setSector] = useState("All");
  const [capital, setCapital] = useState("");
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Auto-fetch on load
  useEffect(() => {
    fetchRecommendations();
  }, []);

  async function fetchRecommendations() {
    setLoading(true);
    setError(null);
    setRecommendations([]);

    try {
      const payload = {
        risk,
        duration,
        sector,
      };
      if (capital) {
        payload.capital = parseFloat(capital);
      }

      const res = await fetch(`${API}/api/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to fetch recommendations");

      setRecommendations(data.recommendations || []);
    } catch (err) {
      setError(err.message || "Error fetching recommendations.");
    } finally {
      setLoading(false);
    }
  }

  function handleRiskChange(newRisk) {
    setRisk(newRisk);
    // Don't auto-fetch yet, let user configure all settings
  }

  function handleDurationChange(newDuration) {
    setDuration(newDuration);
  }

  function handleSectorChange(e) {
    setSector(e.target.value);
  }

  function handleCapitalChange(e) {
    setCapital(e.target.value);
  }

  const selectedRiskProfile = RISK_LEVELS.find((r) => r.id === risk);

  const recommendedSector = useMemo(() => {
    if (sector !== "All") return sector;
    const counts = recommendations.reduce((acc, rec) => {
      if (!rec.sector) return acc;
      acc[rec.sector] = (acc[rec.sector] || 0) + 1;
      return acc;
    }, {});
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    return sorted.length ? sorted[0][0] : "All";
  }, [sector, recommendations]);

  return (
    <div className="advisor-panel">
      <div className="advisor-container">
        {/* Input Section */}
        <div className="advisor-input-section">
          <h2 className="advisor-title">
            🤖 AI Stock Advisor
            <span className="subtitle">
              Get personalized stock recommendations based on your profile
            </span>
          </h2>

          {/* Risk Level Selection */}
          <div className="input-group">
            <label className="group-label">Risk Tolerance</label>
            <div className="risk-buttons">
              {RISK_LEVELS.map((r) => (
                <button
                  key={r.id}
                  type="button"
                  className={`risk-btn ${risk === r.id ? "active" : ""}`}
                  onClick={() => handleRiskChange(r.id)}
                  style={{
                    borderColor: risk === r.id ? r.color : "var(--border-color)",
                    backgroundColor:
                      risk === r.id ? `${r.color}20` : "transparent",
                  }}
                >
                  <div className="risk-icon">{r.icon}</div>
                  <div className="risk-label">{r.label}</div>
                  <div className="risk-desc">{r.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Duration Selection */}
          <div className="input-group">
            <label className="group-label">Investment Duration</label>
            <div className="duration-buttons">
              {DURATIONS.map((d) => (
                <button
                  key={d.id}
                  type="button"
                  className={`duration-btn ${duration === d.id ? "active" : ""}`}
                  onClick={() => handleDurationChange(d.id)}
                >
                  <span className="duration-icon">{d.icon}</span>
                  {d.label}
                </button>
              ))}
            </div>
          </div>

          {/* Sector Selection */}
          <div className="input-group">
            <label className="group-label" htmlFor="sector-select">
              Sector Preference
            </label>
            <select
              id="sector-select"
              className="sector-select"
              value={sector}
              onChange={handleSectorChange}
            >
              {SECTORS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          {/* Capital Input (Optional) */}
          <div className="input-group">
            <label className="group-label" htmlFor="capital-input">
              Investment Capital (Optional)
            </label>
            <div className="capital-input-wrapper">
              <span className="capital-prefix">₹</span>
              <input
                id="capital-input"
                type="number"
                className="capital-input"
                placeholder="e.g., 50000"
                value={capital}
                onChange={handleCapitalChange}
              />
            </div>
          </div>

          {/* Action Button */}
          <button
            type="button"
            className="fetch-btn"
            onClick={fetchRecommendations}
            disabled={loading}
          >
            {loading ? "Loading..." : "Get Recommendations"}
          </button>

          {error && <div className="error-message">{error}</div>}
        </div>

        {/* Results Section */}
        <div className="advisor-results-section">
          <div className="results-heading">
            <h3 className="results-title">
              Recommended Stocks
              {recommendations.length > 0 && (
                <span className="count-badge">{recommendations.length}</span>
              )}
            </h3>
            <div className="sector-summary">
              {sector === "All" ? (
                <>
                  <span>Suggested Sector</span>
                  <strong>{recommendedSector}</strong>
                </>
              ) : (
                <>
                  <span>Selected Sector</span>
                  <strong>{sector}</strong>
                </>
              )}
            </div>
          </div>

          {loading && <div className="loading-spinner">Analyzing stocks...</div>}

          {!loading && recommendations.length === 0 && !error && (
            <div className="empty-state">
              <p>Click "Get Recommendations" to see personalized stock picks</p>
            </div>
          )}

          <div className="recommendations-grid">
            {recommendations.map((rec) => (
              <RecommendationCard
                key={rec.ticker}
                data={rec}
                onViewDetails={() => onSelectSymbol && onSelectSymbol(rec.ticker)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function RecommendationCard({ data, onViewDetails }) {
  const signalColor = {
    BUY: "#4ade80",
    SELL: "#f87171",
    HOLD: "#facc15",
  }[data.signal] || "#64748b";

  const signalBg = {
    BUY: "#dcfce7",
    SELL: "#fee2e2",
    HOLD: "#fef3c7",
  }[data.signal] || "#f1f5f9";

  const upside = data.upside_pct || 0;
  const upsideColor = upside > 0 ? "#4ade80" : "#f87171";
  const layerScores = data.score_breakdown || data.layer_scores || {};
  const newsScore = layerScores.news ?? layerScores.news_sentiment ?? 0;
  const macroScore = layerScores.macro ?? layerScores.macro_trend ?? 0;
  const fundamentalScore = layerScores.fundamental ?? 0;
  const momentumScore = layerScores.momentum ?? 0;

  return (
    <div className="rec-card">
      {/* Header */}
      <div className="rec-header">
        <div className="rec-ticker">
          <span className="ticker-symbol">{data.ticker}</span>
          <span className="ticker-name">{data.name}</span>
          {data.sector && <span className="ticker-meta">{data.sector}</span>}
          {data.sector && (
            <span className="sector-badge">Sector Opportunity · {data.sector}</span>
          )}
        </div>
        <div
          className="rec-signal"
          style={{ backgroundColor: signalBg, borderColor: signalColor }}
        >
          <span style={{ color: signalColor, fontWeight: "bold" }}>
            {data.signal}
          </span>
        </div>
      </div>

      {/* Price Info */}
      <div className="rec-price">
        <span className="price-label">Current Price</span>
        <span className="price-value">₹{data.price}</span>
      </div>

      {/* Confidence & Score */}
      <div className="rec-confidence">
        <div className="conf-item">
          <span className="conf-label">Final Score</span>
          <span className="conf-value">{data.score.toFixed(3)}</span>
        </div>
        <div className="conf-item">
          <span className="conf-label">Confidence</span>
          <span className="conf-value">{Math.round(data.confidence * 100)}%</span>
        </div>
      </div>

      {/* Layer Scores Breakdown */}
      {Object.keys(layerScores).length > 0 && (
        <div className="rec-layers">
          <div className="layer-item">
            <span className="layer-label">📰 News Sentiment</span>
            <span className="layer-value">{(newsScore * 100).toFixed(1)}%</span>
          </div>
          <div className="layer-item">
            <span className="layer-label">📈 Macro Trend</span>
            <span className="layer-value">{(macroScore * 100).toFixed(1)}%</span>
          </div>
          <div className="layer-item">
            <span className="layer-label">🏢 Fundamentals</span>
            <span className="layer-value">{(fundamentalScore * 100).toFixed(1)}%</span>
          </div>
          <div className="layer-item">
            <span className="layer-label">⚡ Momentum</span>
            <span className="layer-value">{(momentumScore * 100).toFixed(1)}%</span>
          </div>
        </div>
      )}

      {/* Targets */}
      <div className="rec-targets">
        <div className="target-item">
          <span className="target-label">🎯 Target</span>
          <span className="target-value">₹{data.target}</span>
          <span className="target-upside" style={{ color: upsideColor }}>
            {upside > 0 ? "+" : ""}
            {upside}%
          </span>
        </div>
        <div className="target-item">
          <span className="target-label">🛑 Stop Loss</span>
          <span className="target-value">₹{data.stoploss}</span>
        </div>
      </div>

      {/* Duration */}
      <div className="rec-duration">
        <span className="duration-label">⏳ Holding Period</span>
        <span className="duration-value">{data.holding_period}</span>
      </div>

      {/* Metrics */}
      <div className="rec-metrics">
        <div className="metric">
          <span className="metric-label">Capital Allocated</span>
          <span className="metric-value">{data.allocated_capital ? `₹${data.allocated_capital.toLocaleString()}` : "—"}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Value at Target</span>
          <span className="metric-value">{data.projected_value_at_target ? `₹${data.projected_value_at_target.toLocaleString()}` : "—"}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Expected Gain</span>
          <span className="metric-value">{data.expected_gain_amount ? `₹${data.expected_gain_amount.toLocaleString()}` : "—"}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Upside</span>
          <span className="metric-value">{upside > 0 ? `+${upside}%` : `${upside}%`}</span>
        </div>
      </div>

      {/* Action Button */}
      <button
        className="rec-action-btn"
        onClick={onViewDetails}
        type="button"
      >
        View Details →
      </button>
    </div>
  );
}
