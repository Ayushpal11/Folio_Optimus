import { useEffect, useRef, useState } from "react";
import { API } from "../utils";

export default function SearchPanel({
  ticker,
  setTicker,
  lookupStock,
  loading,
  error,
  presetSymbols,
  onPresetClick,
}) {
  const [query, setQuery] = useState(ticker || "");
  const [suggestions, setSuggestions] = useState([]);
  const [open, setOpen] = useState(false);
  const [searching, setSearching] = useState(false);
  const debounceRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    setQuery(ticker || "");
  }, [ticker]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const fetchSuggestions = async (text) => {
    if (!text.trim()) {
      setSuggestions([]);
      return;
    }
    setSearching(true);
    try {
      const res = await fetch(`${API}/api/search?q=${encodeURIComponent(text)}`);
      const data = await res.json();
      setSuggestions(data.results || []);
      setOpen(true);
    } catch (e) {
      setSuggestions([]);
    } finally {
      setSearching(false);
    }
  };

  const onChange = (value) => {
    setQuery(value);
    setTicker(value);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchSuggestions(value), 250);
  };

  const chooseSuggestion = (symbol) => {
    setQuery(symbol);
    setTicker(symbol);
    setOpen(false);
    lookupStock(symbol);
  };

  return (
    <section className="search-panel" ref={containerRef}>
      <div className="search-row">
        <div style={{ position: "relative", width: "100%" }}>
          <input
            className="search-input"
            value={query}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && lookupStock()}
            placeholder="Search by name or ticker — e.g. Reliance, TCS, Apple"
          />
          {open && suggestions.length > 0 && (
            <div className="search-suggestions">
              {suggestions.map((item) => (
                <button
                  key={`${item.ticker}-${item.exchange}`}
                  type="button"
                  className="suggestion-item"
                  onClick={() => chooseSuggestion(item.ticker)}
                >
                  <div>{item.name}</div>
                  <div className="suggestion-meta">{item.ticker} · {item.exchange}</div>
                </button>
              ))}
            </div>
          )}
        </div>
        <button className="button primary" onClick={() => lookupStock()} disabled={loading}>
          {loading ? "Loading..." : "Analyse"}
        </button>
      </div>

      <div className="preset-group">
        {presetSymbols.map((symbol) => (
          <button key={symbol} type="button" className="button pill" onClick={() => onPresetClick(symbol)}>
            {symbol.replace(".NS", "").replace(".BO", "")}
          </button>
        ))}
      </div>

      {(error || searching) && (
        <div className="alert error">{searching ? "Searching..." : error}</div>
      )}
    </section>
  );
}
