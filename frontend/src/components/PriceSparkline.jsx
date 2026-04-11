import { ResponsiveContainer, AreaChart, Area } from "recharts";

export default function PriceSparkline({ history }) {
  if (!history?.length) return null;
  const data = history.map((value, index) => ({ index, value }));
  const first = data[0]?.value;
  const last = data[data.length - 1]?.value;
  const up = last >= first;

  return (
    <ResponsiveContainer width="100%" height={72}>
      <AreaChart data={data} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="spark" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={up ? "#00d4aa" : "#ff6b6b"} stopOpacity={0.35} />
            <stop offset="95%" stopColor={up ? "#00d4aa" : "#ff6b6b"} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area type="monotone" dataKey="value" stroke={up ? "#00d4aa" : "#ff6b6b"} fill="url(#spark)" dot={false} strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
