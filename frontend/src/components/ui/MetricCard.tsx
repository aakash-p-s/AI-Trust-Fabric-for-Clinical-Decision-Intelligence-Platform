interface MetricCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  subtextColor?: "green" | "red" | "gray";
}

export default function MetricCard({ label, value, subtext, subtextColor = "gray" }: MetricCardProps) {
  const colorClass =
    subtextColor === "green" ? "text-green-600" : subtextColor === "red" ? "text-red-600" : "text-gray-500";
  return (
    <div className="card">
      <p className="text-xs uppercase text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-semibold">{value}</p>
      {subtext && <p className={`text-xs mt-1 ${colorClass}`}>{subtext}</p>}
    </div>
  );
}
