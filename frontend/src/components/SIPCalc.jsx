import { useState } from "react";
import { ResponsiveContainer, AreaChart, Area, CartesianGrid, XAxis, YAxis, Tooltip, Legend } from "recharts";

export default function SIPCalc() {
  const [monthly, setMonthly] = useState(10000);
  const [years, setYears] = useState(10);
  const [rate, setRate] = useState(12);

  const months = years * 12;
  const r = rate / 100 / 12;
  const fv = monthly * ((Math.pow(1 + r, months) - 1) / r) * (1 + r);
  const invested = monthly * months;
  const gains = fv - invested;

  const chartData = Array.from({ length: years }, (_, i) => {
    const m = (i + 1) * 12;
    const value = monthly * ((Math.pow(1 + r, m) - 1) / r) * (1 + r);
    return { year: `Y${i + 1}`, invested: Math.round(monthly * m), value: Math.round(value) };
  });

  return (
    <section className="sip-panel">
      <div className="sip-grid">
        <div className="card sip-card">
          <div className="section-heading">SIP Parameters</div>
          {[
            ["Monthly Investment (₹)", monthly, setMonthly, 500, 100000, 500],
            ["Duration (Years)", years, setYears, 1, 40, 1],
            ["Expected Return (%/yr)", rate, setRate, 1, 30, 0.5],
          ].map(([label, value, setter, min, max, step]) => (
            <div key={label} className="range-group">
              <div className="range-label-row">
                <span>{label}</span>
                <span>{label.includes("₹") ? `₹${Number(value).toLocaleString("en-IN")}` : `${value}%`}</span>
              </div>
              <input
                className="range-input"
                type="range"
                min={min}
                max={max}
                step={step}
                value={value}
                onChange={(e) => setter(Number(e.target.value))}
              />
            </div>
          ))}

          <div className="sip-summary">
            <div>
              <div className="summary-label">Invested</div>
              <div className="summary-value">₹{Math.round(invested).toLocaleString("en-IN")}</div>
            </div>
            <div>
              <div className="summary-label">Total Value</div>
              <div className="summary-value accent">₹{Math.round(fv).toLocaleString("en-IN")}</div>
            </div>
            <div className="summary-full">
              <div className="summary-label">Wealth Gained</div>
              <div className="summary-value highlight">₹{Math.round(gains).toLocaleString("en-IN")}</div>
              <div className="summary-caption">{((gains / invested) * 100).toFixed(1)}% return on investment</div>
            </div>
          </div>
        </div>

        <div className="card sip-chart-card">
          <div className="section-heading">Growth Projection</div>
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={chartData} margin={{ top: 8, right: 16, left: 16, bottom: 8 }}>
              <defs>
                <linearGradient id="investedGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#7c6aff" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#7c6aff" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="valueGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00d4aa" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#00d4aa" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
              <XAxis dataKey="year" tick={{ fill: "var(--muted)", fontSize: 11 }} />
              <YAxis tick={{ fill: "var(--muted)", fontSize: 10 }} tickFormatter={(value) => `₹${(value / 100000).toFixed(0)}L`} />
              <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border-color)", borderRadius: 12, color: "var(--text)" }} formatter={(value) => [`₹${value.toLocaleString("en-IN")}`, ""]} />
              <Legend wrapperStyle={{ fontSize: 11, color: "var(--muted)" }} />
              <Area type="monotone" dataKey="invested" name="Invested" stroke="#7c6aff" fill="url(#investedGradient)" strokeWidth={2} />
              <Area type="monotone" dataKey="value" name="Portfolio Value" stroke="#00d4aa" fill="url(#valueGradient)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}
