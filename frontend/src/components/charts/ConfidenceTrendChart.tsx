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

interface Props {
  data: TrendPoint[];
  threshold: number;
}

export default function ConfidenceTrendChart({ data, threshold }: Props) {
  return (
    <div className="card">
      <p className="font-semibold mb-1">Confidence Trend</p>
      <p className="text-xs text-gray-500 mb-3">Average confidence over time</p>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis domain={[0, 1]} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(v: number) => v.toFixed(2)} />
          <ReferenceLine y={threshold} stroke="#ef4444" strokeDasharray="4 4" />
          <Line type="monotone" dataKey="avg_confidence" stroke="#3b82f6" strokeWidth={2} dot />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
