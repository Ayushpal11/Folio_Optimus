export const PROD_BACKEND_URL = "https://folio-optimus-1.onrender.com";
export const API = import.meta.env.VITE_API_URL || (typeof window !== "undefined" && window.location.hostname !== "localhost" ? PROD_BACKEND_URL : "http://localhost:8000");

export const INDEX_PRESETS = {
  "Nifty 50": ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS","HINDUNILVR.NS","SBIN.NS","BHARTIARTL.NS","ITC.NS","KOTAKBANK.NS"],
  "Nifty Midcap": ["PERSISTENT.NS","MPHASIS.NS","TRENT.NS","VOLTAS.NS","FEDERALBNK.NS","INDUSTOWER.NS","AUROPHARMA.NS","IDEA.NS","ASHOKLEY.NS","NMDC.NS"],
  "Nifty Smallcap": ["IRFC.NS","RVNL.NS","HUDCO.NS","RAILTEL.NS","SJVN.NS","NBCC.NS","RITES.NS","IRCON.NS","PFCLTD.NS","RECLTD.NS"],
  "US Tech": ["AAPL","MSFT","GOOGL","NVDA","META","AMZN","TSLA","AMD","INTC","CRM"],
};

export const fmt = (n, dec = 2) => typeof n === "number" ? n.toFixed(dec) : "—";
export const fmtCr = (n) => {
  if (n == null || Number.isNaN(n)) return "—";
  if (n >= 1e12) return "₹" + (n / 1e12).toFixed(2) + "T";
  if (n >= 1e7) return "₹" + (n / 1e7).toFixed(1) + "Cr";
  return "₹" + n.toLocaleString();
};
export const fmtUSD = (n) => {
  if (n == null || Number.isNaN(n)) return "—";
  if (n >= 1e12) return "$" + (n / 1e12).toFixed(2) + "T";
  if (n >= 1e9) return "$" + (n / 1e9).toFixed(1) + "B";
  return "$" + n.toLocaleString();
};
export const fmtMktCap = (n, currency) => currency === "INR" ? fmtCr(n) : fmtUSD(n);

export function swingSignal(ret, vol, price, high52, low52) {
  if (ret == null || vol == null || price == null) return null;
  const distFromHigh = (high52 - price) / high52;
  const distFromLow = (price - low52) / (high52 - low52 || 1);
  const momentum = ret;
  const riskReward = momentum / (vol || 1);

  let signal = "HOLD";
  let confidence = 50;
  if (momentum > 0.15 && distFromHigh > 0.08 && riskReward > 0.6) {
    signal = "BUY";
    confidence = Math.min(90, 60 + riskReward * 15);
  }
  if (momentum < -0.05 && distFromLow < 0.3) {
    signal = "SELL";
    confidence = Math.min(85, 55 + Math.abs(momentum) * 80);
  }

  const stopLoss = +(price * (1 - vol * 0.5)).toFixed(2);
  const target = +(price * (1 + vol * 0.8)).toFixed(2);

  return { signal, confidence: +confidence.toFixed(0), stopLoss, target };
}

export function getSignalColor(signal) {
  if (signal === "BUY") return "#00d4aa";
  if (signal === "SELL") return "#ff6b6b";
  return "#ffd93d";
}
