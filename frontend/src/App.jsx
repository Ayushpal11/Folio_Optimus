import { useState, useEffect, useRef } from "react";
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";
 
const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
 
// ── Indian Nifty index constituent presets ──────────────────────────────────
const INDEX_PRESETS = {
  "Nifty 50": ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS","HINDUNILVR.NS","SBIN.NS","BHARTIARTL.NS","ITC.NS","KOTAKBANK.NS"],
  "Nifty Midcap": ["PERSISTENT.NS","MPHASIS.NS","TRENT.NS","VOLTAS.NS","FEDERALBNK.NS","INDUSTOWER.NS","AUROPHARMA.NS","IDEA.NS","ASHOKLEY.NS","NMDC.NS"],
  "Nifty Smallcap": ["IRFC.NS","RVNL.NS","HUDCO.NS","RAILTEL.NS","SJVN.NS","NBCC.NS","RITES.NS","IRCON.NS","PFCLTD.NS","RECLTD.NS"],
  "US Tech": ["AAPL","MSFT","GOOGL","NVDA","META","AMZN","TSLA","AMD","INTC","CRM"],
};
 
const COLORS = ["#00d4aa","#7c6aff","#ff6b6b","#ffd93d","#6bcaff","#ff9f43","#a29bfe","#fd79a8"];
 
// ── Helpers ──────────────────────────────────────────────────────────────────
const fmt = (n, dec = 2) => typeof n === "number" ? n.toFixed(dec) : "—";
const fmtCr = (n) => {
  if (!n) return "—";
  if (n >= 1e12) return "₹" + (n / 1e12).toFixed(2) + "T";
  if (n >= 1e7)  return "₹" + (n / 1e7).toFixed(1) + "Cr";
  return "₹" + n.toLocaleString();
};
const fmtUSD = (n) => {
  if (!n) return "—";
  if (n >= 1e12) return "$" + (n / 1e12).toFixed(2) + "T";
  if (n >= 1e9)  return "$" + (n / 1e9).toFixed(1) + "B";
  return "$" + n.toLocaleString();
};
const fmtMktCap = (n, currency) => currency === "INR" ? fmtCr(n) : fmtUSD(n);
 
// Swing signal calculation from stats
function swingSignal(ret, vol, price, high52, low52) {
  if (!ret || !vol || !price) return null;
  const distFromHigh = (high52 - price) / high52;
  const distFromLow  = (price - low52)  / (high52 - low52 || 1);
  const momentum = ret;
  const riskReward = momentum / (vol || 1);
 
  let signal = "HOLD", confidence = 50;
  if (momentum > 0.15 && distFromHigh > 0.08 && riskReward > 0.6) { signal = "BUY";  confidence = Math.min(90, 60 + riskReward * 15); }
  if (momentum < -0.05 && distFromLow < 0.3)                       { signal = "SELL"; confidence = Math.min(85, 55 + Math.abs(momentum) * 80); }
 
  const stopLoss = +(price * (1 - vol * 0.5)).toFixed(2);
  const target   = +(price * (1 + vol * 0.8)).toFixed(2);
 
  return { signal, confidence: +confidence.toFixed(0), stopLoss, target };
}
 
// ── Sub-components ───────────────────────────────────────────────────────────
function SignalBadge({ signal }) {
  const colors = { BUY: "#00d4aa", SELL: "#ff6b6b", HOLD: "#ffd93d" };
  return (
    <span style={{
      background: colors[signal] + "22", color: colors[signal],
      border: `1px solid ${colors[signal]}44`,
      borderRadius: 6, padding: "2px 10px", fontSize: 11, fontWeight: 700,
      letterSpacing: 1, fontFamily: "monospace"
    }}>{signal}</span>
  );
}
 
function StatCard({ label, value, sub, accent }) {
  return (
    <div style={{
      background: "#111827", border: "1px solid #1f2937",
      borderRadius: 12, padding: "16px 20px", minWidth: 130, flex: 1
    }}>
      <div style={{ color: "#6b7280", fontSize: 11, letterSpacing: 1, textTransform: "uppercase", marginBottom: 6 }}>{label}</div>
      <div style={{ color: accent || "#f9fafb", fontSize: 22, fontWeight: 700, fontFamily: "monospace" }}>{value}</div>
      {sub && <div style={{ color: "#6b7280", fontSize: 11, marginTop: 4 }}>{sub}</div>}
    </div>
  );
}
 
function PriceSparkline({ history }) {
  if (!history?.length) return null;
  const data = history.map((v, i) => ({ i, v }));
  const first = data[0]?.v, last = data[data.length - 1]?.v;
  const up = last >= first;
  return (
    <ResponsiveContainer width="100%" height={60}>
      <AreaChart data={data} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor={up ? "#00d4aa" : "#ff6b6b"} stopOpacity={0.3}/>
            <stop offset="95%" stopColor={up ? "#00d4aa" : "#ff6b6b"} stopOpacity={0}/>
          </linearGradient>
        </defs>
        <Area type="monotone" dataKey="v" stroke={up ? "#00d4aa" : "#ff6b6b"}
          strokeWidth={1.5} fill="url(#sg)" dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
 
// ── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab]               = useState("dashboard");
  const [ticker, setTicker]         = useState("RELIANCE.NS");
  const [stockData, setStockData]   = useState(null);
  const [priceHistory, setPriceHistory] = useState([]);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState(null);
 
  const [portfolio, setPortfolio]   = useState([]);
  const [batchData, setBatchData]   = useState(null);
  const [batchLoading, setBatchLoading] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState("Nifty 50");
  const [capital, setCapital]       = useState(100000);
 
  // ── Fetch single stock ──────────────────────────────────────────────────
  async function lookupStock(t = ticker) {
    setLoading(true); setError(null); setStockData(null); setPriceHistory([]);
    try {
      const res  = await fetch(`${API}/api/stock/${t.trim().toUpperCase()}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      setStockData(data);
 
      // fetch price history for sparkline
      const hist = await fetch(`${API}/api/price-history/${t.trim().toUpperCase()}`);
      if (hist.ok) {
        const hd = await hist.json();
        setPriceHistory(hd.prices || []);
      }
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }
 
  // ── Fetch batch / screener ──────────────────────────────────────────────
  async function loadBatch(tickers) {
    setBatchLoading(true); setBatchData(null);
    try {
      const res  = await fetch(`${API}/api/batch-stats`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tickers }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      setBatchData(data);
    } catch (e) { setError(e.message); }
    finally { setBatchLoading(false); }
  }
 
  useEffect(() => { lookupStock("RELIANCE.NS"); }, []);
  useEffect(() => { loadBatch(INDEX_PRESETS[selectedPreset]); }, [selectedPreset]);
 
  // ── Derived swing data for screener table ───────────────────────────────
  const screenerRows = batchData
    ? Object.keys(batchData.annualised_return).map((t) => {
        const ret = batchData.annualised_return[t];
        const vol = batchData.annualised_volatility[t];
        const sw  = swingSignal(ret, vol, 0, 1, 0);
        return { ticker: t, ret, vol, sharpe: ret / (vol || 1), signal: sw?.signal, confidence: sw?.confidence };
      }).sort((a, b) => b.sharpe - a.sharpe)
    : [];
 
  // ── Radar chart data ────────────────────────────────────────────────────
  const radarData = stockData ? [
    { metric: "Return",     value: Math.min(100, Math.abs(stockData.annualised_return) * 200) },
    { metric: "Stability",  value: Math.max(0, 100 - stockData.annualised_volatility * 200) },
    { metric: "Value",      value: stockData.pe_ratio ? Math.max(0, 100 - stockData.pe_ratio) : 50 },
    { metric: "Momentum",   value: stockData.annualised_return > 0 ? 70 : 30 },
    { metric: "Range Pos",  value: stockData["52w_high"] && stockData.current_price
        ? Math.round(((stockData.current_price - stockData["52w_low"]) /
          (stockData["52w_high"] - stockData["52w_low"])) * 100) : 50 },
  ] : [];
 
  const sw = stockData ? swingSignal(
    stockData.annualised_return, stockData.annualised_volatility,
    stockData.current_price, stockData["52w_high"], stockData["52w_low"]
  ) : null;
 
  // ── Correlation heatmap data ────────────────────────────────────────────
  const corrKeys = batchData ? Object.keys(batchData.correlation_matrix) : [];
 
  // ── Render ──────────────────────────────────────────────────────────────
  return (
    <div style={{
      minHeight: "100vh", background: "#0a0e1a", color: "#f0f0f0",
      fontFamily: "'IBM Plex Mono', 'Courier New', monospace",
    }}>
      {/* Google font */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 6px; } ::-webkit-scrollbar-track { background: #0a0e1a; }
        ::-webkit-scrollbar-thumb { background: #1f2937; border-radius: 3px; }
        input, select, button { font-family: inherit; }
        table { border-collapse: collapse; width: 100%; }
        th { color: #6b7280; font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase; padding: 8px 12px; border-bottom: 1px solid #1f2937; text-align: left; }
        td { padding: 10px 12px; border-bottom: 1px solid #111827; font-size: 13px; }
        tr:hover td { background: #111827; }
        .tab-btn { background: none; border: none; color: #6b7280; padding: "10px 20px"; cursor: pointer; font-size: 13px; letter-spacing: 1px; text-transform: uppercase; border-bottom: 2px solid transparent; transition: all .2s; }
        .tab-btn.active { color: #00d4aa; border-bottom-color: #00d4aa; }
        .tab-btn:hover { color: #f0f0f0; }
        .lookup-btn { background: #00d4aa; color: #0a0e1a; border: none; border-radius: 8px; padding: 10px 22px; cursor: pointer; font-weight: 700; font-size: 13px; transition: opacity .2s; }
        .lookup-btn:hover { opacity: .85; } .lookup-btn:disabled { opacity: .5; cursor: not-allowed; }
        .inp { background: #111827; border: 1px solid #1f2937; color: #f0f0f0; border-radius: 8px; padding: 10px 14px; font-size: 14px; outline: none; transition: border .2s; }
        .inp:focus { border-color: #00d4aa44; }
        .preset-btn { background: #111827; border: 1px solid #1f2937; color: #9ca3af; border-radius: 8px; padding: 7px 14px; cursor: pointer; font-size: 12px; transition: all .2s; white-space: nowrap; }
        .preset-btn.active { background: #00d4aa22; border-color: #00d4aa; color: #00d4aa; }
        .preset-btn:hover { border-color: #374151; color: #f0f0f0; }
        .card { background: #111827; border: 1px solid #1f2937; border-radius: 14px; padding: 20px; }
      `}</style>
 
      {/* Header */}
      <div style={{ borderBottom: "1px solid #1f2937", padding: "16px 32px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#00d4aa", boxShadow: "0 0 8px #00d4aa" }} />
          <span style={{ fontSize: 15, fontWeight: 700, letterSpacing: 2, color: "#f0f0f0" }}>PORTFOLIO OPTIMIZER</span>
          <span style={{ fontSize: 11, color: "#374151", letterSpacing: 1 }}>v2.0 · NSE/BSE/US</span>
        </div>
        <div style={{ fontSize: 11, color: "#4b5563" }}>{new Date().toLocaleDateString("en-IN", { weekday:"short", day:"numeric", month:"short", year:"numeric" })}</div>
      </div>
 
      {/* Tabs */}
      <div style={{ padding: "0 32px", borderBottom: "1px solid #1f2937", display: "flex", gap: 4 }}>
        {[["dashboard","Dashboard"],["screener","Screener"],["swing","Swing Signals"],["sip","SIP Calc"]].map(([id, label]) => (
          <button key={id} className={`tab-btn ${tab===id?"active":""}`}
            style={{ padding: "14px 20px" }}
            onClick={() => setTab(id)}>{label}</button>
        ))}
      </div>
 
      <div style={{ padding: "24px 32px", maxWidth: 1400, margin: "0 auto" }}>
 
        {/* ── DASHBOARD TAB ── */}
        {tab === "dashboard" && (
          <div>
            {/* Search bar */}
            <div style={{ display: "flex", gap: 10, marginBottom: 24, alignItems: "center" }}>
              <input className="inp" value={ticker} onChange={e => setTicker(e.target.value)}
                onKeyDown={e => e.key === "Enter" && lookupStock()}
                placeholder="RELIANCE.NS · TCS.NS · AAPL · INFY.NS"
                style={{ flex: 1, maxWidth: 380 }} />
              <button className="lookup-btn" onClick={() => lookupStock()} disabled={loading}>
                {loading ? "LOADING..." : "ANALYSE"}
              </button>
              <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
                {["RELIANCE.NS","TCS.NS","HDFCBANK.NS","AAPL","NIFTY50.NS"].map(t => (
                  <button key={t} className="preset-btn" onClick={() => { setTicker(t); lookupStock(t); }}>{t.replace(".NS","")}</button>
                ))}
              </div>
            </div>
 
            {error && <div style={{ background:"#ff6b6b22", border:"1px solid #ff6b6b44", borderRadius:10, padding:"12px 16px", color:"#ff6b6b", marginBottom:16, fontSize:13 }}>{error}</div>}
 
            {stockData && (
              <div>
                {/* Top stat cards */}
                <div style={{ display:"flex", gap:12, marginBottom:20, flexWrap:"wrap" }}>
                  <StatCard label="Current Price"
                    value={stockData.currency === "INR" ? `₹${stockData.current_price?.toLocaleString("en-IN")}` : `$${stockData.current_price}`}
                    sub={stockData.name} accent="#f9fafb" />
                  <StatCard label="Ann. Return" value={`${(stockData.annualised_return * 100).toFixed(1)}%`}
                    sub="1-year annualised" accent={stockData.annualised_return > 0 ? "#00d4aa" : "#ff6b6b"} />
                  <StatCard label="Volatility" value={`${(stockData.annualised_volatility * 100).toFixed(1)}%`}
                    sub="Annualised σ" accent="#ffd93d" />
                  <StatCard label="P/E Ratio" value={stockData.pe_ratio ? fmt(stockData.pe_ratio) : "—"}
                    sub="Trailing" accent="#7c6aff" />
                  <StatCard label="Market Cap" value={fmtMktCap(stockData.market_cap, stockData.currency)}
                    sub={stockData.sector} accent="#6bcaff" />
                  {sw && <StatCard label="Swing Signal" value={sw.signal}
                    sub={`${sw.confidence}% confidence`}
                    accent={sw.signal==="BUY"?"#00d4aa":sw.signal==="SELL"?"#ff6b6b":"#ffd93d"} />}
                </div>
 
                {/* Charts row */}
                <div style={{ display:"grid", gridTemplateColumns:"1fr 340px", gap:16, marginBottom:16 }}>
 
                  {/* Price range bar */}
                  <div className="card">
                    <div style={{ fontSize:11, color:"#6b7280", letterSpacing:1, marginBottom:14, textTransform:"uppercase" }}>52-Week Range</div>
                    <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:8 }}>
                      <span style={{ fontSize:12, color:"#6b7280", minWidth:60 }}>₹{stockData["52w_low"]?.toLocaleString("en-IN")}</span>
                      <div style={{ flex:1, height:6, background:"#1f2937", borderRadius:3, position:"relative" }}>
                        <div style={{
                          position:"absolute", left:0, top:0, height:"100%", borderRadius:3,
                          background:"linear-gradient(90deg,#ff6b6b,#ffd93d,#00d4aa)",
                          width: `${Math.round(((stockData.current_price - stockData["52w_low"]) / ((stockData["52w_high"] - stockData["52w_low"]) || 1)) * 100)}%`
                        }}/>
                        <div style={{
                          position:"absolute", top:-4, width:14, height:14, borderRadius:"50%",
                          background:"#f0f0f0", border:"2px solid #0a0e1a",
                          left: `calc(${Math.round(((stockData.current_price - stockData["52w_low"]) / ((stockData["52w_high"] - stockData["52w_low"]) || 1)) * 100)}% - 7px)`
                        }}/>
                      </div>
                      <span style={{ fontSize:12, color:"#6b7280", minWidth:60, textAlign:"right" }}>₹{stockData["52w_high"]?.toLocaleString("en-IN")}</span>
                    </div>
                    <div style={{ textAlign:"center", fontSize:13, color:"#f0f0f0", fontWeight:600 }}>
                      Current: {stockData.currency==="INR"?"₹":"$"}{stockData.current_price?.toLocaleString("en-IN")} &nbsp;·&nbsp;
                      {Math.round(((stockData.current_price - stockData["52w_low"]) / ((stockData["52w_high"] - stockData["52w_low"]) || 1)) * 100)}% from low
                    </div>
 
                    {/* Sparkline */}
                    <div style={{ marginTop:20 }}>
                      <div style={{ fontSize:11, color:"#6b7280", letterSpacing:1, marginBottom:8, textTransform:"uppercase" }}>Price History</div>
                      <PriceSparkline history={priceHistory} />
                    </div>
 
                    {/* Swing details */}
                    {sw && (
                      <div style={{ marginTop:20, display:"flex", gap:10, flexWrap:"wrap" }}>
                        <div style={{ flex:1, background:"#0a0e1a", borderRadius:10, padding:"12px 16px", border:"1px solid #1f2937" }}>
                          <div style={{ fontSize:10, color:"#6b7280", letterSpacing:1, marginBottom:6 }}>STOP LOSS</div>
                          <div style={{ color:"#ff6b6b", fontWeight:700, fontSize:16 }}>{stockData.currency==="INR"?"₹":"$"}{sw.stopLoss?.toLocaleString("en-IN")}</div>
                        </div>
                        <div style={{ flex:1, background:"#0a0e1a", borderRadius:10, padding:"12px 16px", border:"1px solid #1f2937" }}>
                          <div style={{ fontSize:10, color:"#6b7280", letterSpacing:1, marginBottom:6 }}>TARGET</div>
                          <div style={{ color:"#00d4aa", fontWeight:700, fontSize:16 }}>{stockData.currency==="INR"?"₹":"$"}{sw.target?.toLocaleString("en-IN")}</div>
                        </div>
                        <div style={{ flex:1, background:"#0a0e1a", borderRadius:10, padding:"12px 16px", border:"1px solid #1f2937" }}>
                          <div style={{ fontSize:10, color:"#6b7280", letterSpacing:1, marginBottom:6 }}>SIGNAL</div>
                          <SignalBadge signal={sw.signal} />
                          <div style={{ fontSize:10, color:"#6b7280", marginTop:4 }}>{sw.confidence}% conf.</div>
                        </div>
                      </div>
                    )}
                  </div>
 
                  {/* Radar chart */}
                  <div className="card">
                    <div style={{ fontSize:11, color:"#6b7280", letterSpacing:1, marginBottom:4, textTransform:"uppercase" }}>Stock Profile</div>
                    <ResponsiveContainer width="100%" height={240}>
                      <RadarChart data={radarData}>
                        <PolarGrid stroke="#1f2937" />
                        <PolarAngleAxis dataKey="metric" tick={{ fill:"#6b7280", fontSize:11 }} />
                        <Radar dataKey="value" stroke="#00d4aa" fill="#00d4aa" fillOpacity={0.2} strokeWidth={2} />
                      </RadarChart>
                    </ResponsiveContainer>
                    <div style={{ fontSize:11, color:"#4b5563", textAlign:"center", marginTop:4 }}>
                      {stockData.industry} · {stockData.sector}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
 
        {/* ── SCREENER TAB ── */}
        {tab === "screener" && (
          <div>
            <div style={{ display:"flex", gap:8, marginBottom:20, flexWrap:"wrap", alignItems:"center" }}>
              {Object.keys(INDEX_PRESETS).map(p => (
                <button key={p} className={`preset-btn ${selectedPreset===p?"active":""}`}
                  onClick={() => setSelectedPreset(p)}>{p}</button>
              ))}
              {batchLoading && <span style={{ fontSize:12, color:"#6b7280" }}>Fetching data...</span>}
            </div>
 
            {batchData && (
              <div>
                {/* Return vs Volatility bar chart */}
                <div className="card" style={{ marginBottom:16 }}>
                  <div style={{ fontSize:11, color:"#6b7280", letterSpacing:1, marginBottom:16, textTransform:"uppercase" }}>Return vs Volatility — {selectedPreset}</div>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={screenerRows.slice(0,10)} margin={{ top:4, right:20, left:0, bottom:30 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                      <XAxis dataKey="ticker" tick={{ fill:"#6b7280", fontSize:10 }} angle={-30} textAnchor="end" />
                      <YAxis tick={{ fill:"#6b7280", fontSize:10 }} tickFormatter={v => `${(v*100).toFixed(0)}%`} />
                      <Tooltip contentStyle={{ background:"#111827", border:"1px solid #1f2937", borderRadius:8, fontSize:12 }}
                        formatter={(v, n) => [`${(v*100).toFixed(1)}%`, n]} />
                      <Legend wrapperStyle={{ fontSize:11, color:"#6b7280" }} />
                      <Bar dataKey="ret"  name="Ann. Return"     fill="#00d4aa" radius={[4,4,0,0]} />
                      <Bar dataKey="vol"  name="Volatility"      fill="#ff6b6b" radius={[4,4,0,0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
 
                {/* Sharpe ratio chart */}
                <div className="card" style={{ marginBottom:16 }}>
                  <div style={{ fontSize:11, color:"#6b7280", letterSpacing:1, marginBottom:16, textTransform:"uppercase" }}>Sharpe Ratio Ranking</div>
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={screenerRows.slice(0,10)} layout="vertical" margin={{ top:0, right:40, left:80, bottom:0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
                      <XAxis type="number" tick={{ fill:"#6b7280", fontSize:10 }} tickFormatter={v => v.toFixed(2)} />
                      <YAxis type="category" dataKey="ticker" tick={{ fill:"#9ca3af", fontSize:10 }} width={80} />
                      <Tooltip contentStyle={{ background:"#111827", border:"1px solid #1f2937", borderRadius:8, fontSize:12 }}
                        formatter={v => [v.toFixed(3), "Sharpe"]} />
                      <Bar dataKey="sharpe" name="Sharpe Ratio" fill="#7c6aff" radius={[0,4,4,0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
 
                {/* Screener table */}
                <div className="card">
                  <div style={{ fontSize:11, color:"#6b7280", letterSpacing:1, marginBottom:14, textTransform:"uppercase" }}>Stock Screener — {selectedPreset}</div>
                  <div style={{ overflowX:"auto" }}>
                    <table>
                      <thead>
                        <tr>
                          <th>Ticker</th><th>Ann. Return</th><th>Volatility</th>
                          <th>Sharpe</th><th>Signal</th><th>Confidence</th>
                        </tr>
                      </thead>
                      <tbody>
                        {screenerRows.map((r, i) => (
                          <tr key={r.ticker} style={{ cursor:"pointer" }}
                            onClick={() => { setTab("dashboard"); setTicker(r.ticker); lookupStock(r.ticker); }}>
                            <td>
                              <span style={{ color: i < 3 ? "#00d4aa" : "#f0f0f0", fontWeight: i < 3 ? 700 : 400 }}>
                                {i < 3 ? "★ " : ""}{r.ticker}
                              </span>
                            </td>
                            <td style={{ color: r.ret > 0 ? "#00d4aa" : "#ff6b6b" }}>
                              {r.ret > 0 ? "+" : ""}{(r.ret * 100).toFixed(1)}%
                            </td>
                            <td style={{ color: "#ffd93d" }}>{(r.vol * 100).toFixed(1)}%</td>
                            <td style={{ color: r.sharpe > 1 ? "#00d4aa" : r.sharpe > 0.5 ? "#ffd93d" : "#9ca3af" }}>
                              {r.sharpe.toFixed(3)}
                            </td>
                            <td><SignalBadge signal={r.signal || "HOLD"} /></td>
                            <td>
                              <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                                <div style={{ flex:1, height:4, background:"#1f2937", borderRadius:2, maxWidth:80 }}>
                                  <div style={{ width:`${r.confidence||50}%`, height:"100%", borderRadius:2,
                                    background: r.signal==="BUY"?"#00d4aa":r.signal==="SELL"?"#ff6b6b":"#ffd93d" }}/>
                                </div>
                                <span style={{ fontSize:11, color:"#6b7280" }}>{r.confidence||50}%</span>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
 
        {/* ── SWING SIGNALS TAB ── */}
        {tab === "swing" && (
          <div>
            <div style={{ display:"flex", gap:8, marginBottom:20, flexWrap:"wrap" }}>
              {Object.keys(INDEX_PRESETS).map(p => (
                <button key={p} className={`preset-btn ${selectedPreset===p?"active":""}`}
                  onClick={() => setSelectedPreset(p)}>{p}</button>
              ))}
            </div>
 
            {batchData && (
              <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(300px,1fr))", gap:14 }}>
                {screenerRows.map((r) => {
                  const sw2 = swingSignal(r.ret, r.vol, 100, 130, 70);
                  const pct = (r.ret * 100).toFixed(1);
                  return (
                    <div key={r.ticker} className="card" style={{ cursor:"pointer",
                      borderColor: r.signal==="BUY"?"#00d4aa33":r.signal==="SELL"?"#ff6b6b33":"#1f2937" }}
                      onClick={() => { setTab("dashboard"); setTicker(r.ticker); lookupStock(r.ticker); }}>
                      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:12 }}>
                        <div>
                          <div style={{ fontWeight:700, fontSize:14, color:"#f0f0f0" }}>{r.ticker}</div>
                          <div style={{ fontSize:11, color:"#6b7280", marginTop:2 }}>Ann. return: <span style={{ color: r.ret>0?"#00d4aa":"#ff6b6b" }}>{r.ret>0?"+":""}{pct}%</span></div>
                        </div>
                        <SignalBadge signal={r.signal || "HOLD"} />
                      </div>
                      <div style={{ display:"flex", gap:8, marginBottom:12 }}>
                        <div style={{ flex:1, background:"#0a0e1a", borderRadius:8, padding:"8px 12px" }}>
                          <div style={{ fontSize:10, color:"#6b7280" }}>STOP LOSS</div>
                          <div style={{ fontSize:13, color:"#ff6b6b", fontWeight:600 }}>–{(r.vol * 50).toFixed(1)}%</div>
                        </div>
                        <div style={{ flex:1, background:"#0a0e1a", borderRadius:8, padding:"8px 12px" }}>
                          <div style={{ fontSize:10, color:"#6b7280" }}>TARGET</div>
                          <div style={{ fontSize:13, color:"#00d4aa", fontWeight:600 }}>+{(r.vol * 80).toFixed(1)}%</div>
                        </div>
                        <div style={{ flex:1, background:"#0a0e1a", borderRadius:8, padding:"8px 12px" }}>
                          <div style={{ fontSize:10, color:"#6b7280" }}>SHARPE</div>
                          <div style={{ fontSize:13, color:"#7c6aff", fontWeight:600 }}>{r.sharpe.toFixed(2)}</div>
                        </div>
                      </div>
                      <div style={{ height:4, background:"#1f2937", borderRadius:2 }}>
                        <div style={{ width:`${r.confidence||50}%`, height:"100%", borderRadius:2,
                          background: r.signal==="BUY"?"#00d4aa":r.signal==="SELL"?"#ff6b6b":"#ffd93d",
                          transition:"width .6s ease" }}/>
                      </div>
                      <div style={{ fontSize:10, color:"#4b5563", marginTop:6, textAlign:"right" }}>Volatility: {(r.vol*100).toFixed(1)}%</div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
 
        {/* ── SIP CALCULATOR TAB ── */}
        {tab === "sip" && (
          <SIPCalc />
        )}
      </div>
    </div>
  );
}
 
// ── SIP Calculator Component ─────────────────────────────────────────────────
function SIPCalc() {
  const [monthly, setMonthly] = useState(10000);
  const [years,   setYears]   = useState(10);
  const [rate,    setRate]    = useState(12);
 
  const months  = years * 12;
  const r       = rate / 100 / 12;
  const fv      = monthly * ((Math.pow(1 + r, months) - 1) / r) * (1 + r);
  const invested = monthly * months;
  const gains    = fv - invested;
 
  const chartData = Array.from({ length: years }, (_, i) => {
    const m  = (i + 1) * 12;
    const v  = monthly * ((Math.pow(1 + r, m) - 1) / r) * (1 + r);
    const inv = monthly * m;
    return { year: `Y${i+1}`, invested: Math.round(inv), value: Math.round(v) };
  });
 
  return (
    <div>
      <div style={{ display:"grid", gridTemplateColumns:"360px 1fr", gap:20 }}>
        <div className="card">
          <div style={{ fontSize:11, color:"#6b7280", letterSpacing:1, marginBottom:20, textTransform:"uppercase" }}>SIP Parameters</div>
          {[
            ["Monthly Investment (₹)", monthly, setMonthly, 500, 100000, 500],
            ["Duration (Years)", years, setYears, 1, 40, 1],
            ["Expected Return (%/yr)", rate, setRate, 1, 30, 0.5],
          ].map(([label, val, setter, min, max, step]) => (
            <div key={label} style={{ marginBottom:20 }}>
              <div style={{ display:"flex", justifyContent:"space-between", marginBottom:8 }}>
                <span style={{ fontSize:12, color:"#9ca3af" }}>{label}</span>
                <span style={{ fontSize:14, fontWeight:700, color:"#00d4aa" }}>
                  {label.includes("₹") ? `₹${Number(val).toLocaleString("en-IN")}` : val}{label.includes("%") ? "%" : ""}
                </span>
              </div>
              <input type="range" min={min} max={max} step={step} value={val}
                onChange={e => setter(Number(e.target.value))}
                style={{ width:"100%", accentColor:"#00d4aa" }} />
            </div>
          ))}
 
          <div style={{ borderTop:"1px solid #1f2937", paddingTop:16, display:"grid", gridTemplateColumns:"1fr 1fr", gap:10 }}>
            <div style={{ background:"#0a0e1a", borderRadius:10, padding:"12px 14px" }}>
              <div style={{ fontSize:10, color:"#6b7280", marginBottom:4 }}>INVESTED</div>
              <div style={{ fontSize:16, fontWeight:700 }}>₹{Math.round(invested).toLocaleString("en-IN")}</div>
            </div>
            <div style={{ background:"#0a0e1a", borderRadius:10, padding:"12px 14px" }}>
              <div style={{ fontSize:10, color:"#6b7280", marginBottom:4 }}>TOTAL VALUE</div>
              <div style={{ fontSize:16, fontWeight:700, color:"#00d4aa" }}>₹{Math.round(fv).toLocaleString("en-IN")}</div>
            </div>
            <div style={{ background:"#0a0e1a", borderRadius:10, padding:"12px 14px", gridColumn:"span 2" }}>
              <div style={{ fontSize:10, color:"#6b7280", marginBottom:4 }}>WEALTH GAINED</div>
              <div style={{ fontSize:20, fontWeight:700, color:"#7c6aff" }}>₹{Math.round(gains).toLocaleString("en-IN")}</div>
              <div style={{ fontSize:11, color:"#4b5563", marginTop:2 }}>
                {((gains / invested) * 100).toFixed(1)}% return on investment
              </div>
            </div>
          </div>
        </div>
 
        <div className="card">
          <div style={{ fontSize:11, color:"#6b7280", letterSpacing:1, marginBottom:16, textTransform:"uppercase" }}>Growth Projection</div>
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={chartData} margin={{ top:4, right:20, left:20, bottom:4 }}>
              <defs>
                <linearGradient id="iv" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#7c6aff" stopOpacity={0.3}/><stop offset="95%" stopColor="#7c6aff" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="vl" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00d4aa" stopOpacity={0.3}/><stop offset="95%" stopColor="#00d4aa" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="year" tick={{ fill:"#6b7280", fontSize:11 }} />
              <YAxis tick={{ fill:"#6b7280", fontSize:10 }} tickFormatter={v => `₹${(v/100000).toFixed(0)}L`} />
              <Tooltip contentStyle={{ background:"#111827", border:"1px solid #1f2937", borderRadius:8, fontSize:12 }}
                formatter={v => [`₹${v.toLocaleString("en-IN")}`, ""]} />
              <Legend wrapperStyle={{ fontSize:11, color:"#6b7280" }} />
              <Area type="monotone" dataKey="invested" name="Amount Invested" stroke="#7c6aff" fill="url(#iv)" strokeWidth={2} />
              <Area type="monotone" dataKey="value"    name="Portfolio Value"  stroke="#00d4aa" fill="url(#vl)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}