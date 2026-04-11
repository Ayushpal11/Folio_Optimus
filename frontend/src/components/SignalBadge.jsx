import { getSignalColor } from "../utils";

export default function SignalBadge({ signal }) {
  const color = getSignalColor(signal);
  return (
    <span className="signal-badge" style={{ color, borderColor: `${color}44`, backgroundColor: `${color}22` }}>
      {signal || "HOLD"}
    </span>
  );
}
