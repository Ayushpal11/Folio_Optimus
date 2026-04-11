export default function TopBar({ theme, onToggleTheme }) {
  return (
    <header className="topbar">
      <div className="topbar-brand">
        <span className="brand-dot" />
        <div>
          <div className="brand-title">Portfolio Optimizer</div>
          <div className="brand-caption">NSE / BSE / US</div>
        </div>
      </div>
      <button className="theme-toggle" onClick={onToggleTheme} type="button">
        {theme === "dark" ? "Light mode" : "Dark mode"}
      </button>
    </header>
  );
}
