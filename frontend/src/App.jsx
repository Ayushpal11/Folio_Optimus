import { useEffect, useState } from "react";
import { API, INDEX_PRESETS, swingSignal } from "./utils";
import TopBar from "./components/TopBar";
import TabBar from "./components/TabBar";
import SearchPanel from "./components/SearchPanel";
import StockDashboard from "./components/StockDashboard";
import ScreenerPanel from "./components/ScreenerPanel";
import SwingPanel from "./components/SwingPanel";
import SIPCalc from "./components/SIPCalc";

const DEFAULT_TICKER = "RELIANCE.NS";

function getInitialTheme() {
  if (typeof window === "undefined") return "dark";
  const saved = window.localStorage.getItem("folio-theme");
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function App() {
  const [theme, setTheme] = useState(getInitialTheme);
  const [tab, setTab] = useState("dashboard");
  const [ticker, setTicker] = useState(DEFAULT_TICKER);
  const [stockData, setStockData] = useState(null);
  const [priceHistory, setPriceHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [batchData, setBatchData] = useState(null);
  const [batchLoading, setBatchLoading] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState("Nifty 50");

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("folio-theme", theme);
  }, [theme]);

  useEffect(() => {
    lookupStock(DEFAULT_TICKER);
  }, []);

  useEffect(() => {
    loadBatch(INDEX_PRESETS[selectedPreset]);
  }, [selectedPreset]);

  async function lookupStock(symbol = ticker) {
    const normalized = symbol.trim().toUpperCase();
    if (!normalized) return;

    setLoading(true);
    setError(null);
    setStockData(null);
    setPriceHistory([]);

    try {
      const stockRes = await fetch(`${API}/api/stock/${normalized}`);
      const stockJson = await stockRes.json();
      if (!stockRes.ok) throw new Error(stockJson.detail || "Unable to load stock data");
      setStockData(stockJson);

      const historyRes = await fetch(`${API}/api/price-history/${normalized}`);
      if (historyRes.ok) {
        const historyJson = await historyRes.json();
        setPriceHistory(historyJson.prices || []);
      }
    } catch (err) {
      setError(err.message || "Error fetching stock info.");
    } finally {
      setLoading(false);
    }
  }

  async function loadBatch(tickers) {
    setBatchLoading(true);
    setBatchData(null);
    setError(null);

    try {
      const res = await fetch(`${API}/api/batch-stats`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tickers }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Unable to load batch stats");
      setBatchData(data);
    } catch (err) {
      setError(err.message || "Error fetching batch stats.");
    } finally {
      setBatchLoading(false);
    }
  }

  const sw = stockData
    ? swingSignal(
        stockData.annualised_return,
        stockData.annualised_volatility,
        stockData.current_price,
        stockData["52w_high"],
        stockData["52w_low"],
      )
    : null;

  const radarData = stockData
    ? [
        { metric: "Return", value: Math.min(100, Math.abs(stockData.annualised_return) * 200) },
        { metric: "Stability", value: Math.max(0, 100 - stockData.annualised_volatility * 200) },
        { metric: "Value", value: stockData.pe_ratio ? Math.max(0, 100 - stockData.pe_ratio) : 50 },
        { metric: "Momentum", value: stockData.annualised_return > 0 ? 70 : 30 },
        { metric: "Range Pos", value: stockData["52w_high"] && stockData.current_price
          ? Math.round(((stockData.current_price - stockData["52w_low"]) / ((stockData["52w_high"] - stockData["52w_low"]) || 1)) * 100)
          : 50 },
      ]
    : [];

  return (
    <div className="app-shell">
      <TopBar theme={theme} onToggleTheme={() => setTheme(theme === "dark" ? "light" : "dark")} />
      <TabBar activeTab={tab} onChange={setTab} />

      <main className="page-container">
        {tab === "dashboard" && (
          <>
            <SearchPanel
              ticker={ticker}
              setTicker={setTicker}
              lookupStock={lookupStock}
              loading={loading}
              error={error}
              presetSymbols={["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "AAPL", "NIFTY50.NS"]}
              onPresetClick={(symbol) => { setTicker(symbol); lookupStock(symbol); }}
            />
            <StockDashboard stockData={stockData} priceHistory={priceHistory} sw={sw} radarData={radarData} />
          </>
        )}

        {tab === "screener" && (
          <ScreenerPanel
            batchData={batchData}
            selectedPreset={selectedPreset}
            setSelectedPreset={setSelectedPreset}
            batchLoading={batchLoading}
            onSelectSymbol={(symbol) => { setTab("dashboard"); setTicker(symbol); lookupStock(symbol); }}
          />
        )}

        {tab === "swing" && (
          <SwingPanel
            batchData={batchData}
            selectedPreset={selectedPreset}
            setSelectedPreset={setSelectedPreset}
            batchLoading={batchLoading}
            onSelectSymbol={(symbol) => { setTab("dashboard"); setTicker(symbol); lookupStock(symbol); }}
          />
        )}

        {tab === "sip" && <SIPCalc />}
      </main>
    </div>
  );
}
