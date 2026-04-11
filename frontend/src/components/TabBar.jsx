const tabs = [
  ["dashboard", "Dashboard"],
  ["screener", "Screener"],
  ["swing", "Swing Signals"],
  ["sip", "SIP Calc"],
];

export default function TabBar({ activeTab, onChange }) {
  return (
    <nav className="tabbar">
      {tabs.map(([id, label]) => (
        <button
          key={id}
          type="button"
          className={`tab-btn ${activeTab === id ? "active" : ""}`}
          onClick={() => onChange(id)}
        >
          {label}
        </button>
      ))}
    </nav>
  );
}
