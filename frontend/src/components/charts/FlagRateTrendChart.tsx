import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TrendPoint } from "../../lib/types";

const FLAG_RATE_THRESHOLD_PCT = 10;

export default function FlagRateTrendChart({ data }: { data: TrendPoint[] }) {
  return (
    <div className="card">
      <p className="font-semibold mb-1">Flag-Rate Trend</p>
      <p className="text-xs text-gray-500 mb-3">% of predictions flagged over time</p>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} unit="%" />
          <Tooltip formatter={(v: number) => `${v.toFixed(1)}%`} />
          <ReferenceLine y={FLAG_RATE_THRESHOLD_PCT} stroke="#ef4444" strokeDasharray="4 4" />
          <Line type="monotone" dataKey="pct_flagged" stroke="#f59e0b" strokeWidth={2} dot />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
