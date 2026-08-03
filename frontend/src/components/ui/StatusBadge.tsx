interface StatusBadgeProps {
  status: "Cleared" | "Flagged" | "Active" | "High" | "Low" | "Drift Detected" | "Normal";
}

const CLASS_MAP: Record<string, string> = {
  Cleared: "badge-green",
  Normal: "badge-green",
  Flagged: "badge-amber",
  High: "badge-red",
  "Drift Detected": "badge-amber",
  Active: "badge-amber",
  Low: "badge-gray",
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const className = CLASS_MAP[status] || "badge-gray";
  return <span className={className}>{status}</span>;
}
