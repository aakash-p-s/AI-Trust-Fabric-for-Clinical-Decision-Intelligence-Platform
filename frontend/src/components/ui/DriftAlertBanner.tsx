import { AlertTriangle } from "lucide-react";
import type { DriftAlert } from "../../lib/types";

interface Props {
  alert: DriftAlert;
  onViewDetails: () => void;
}

export default function DriftAlertBanner({ alert, onViewDetails }: Props) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-amber-300 bg-amber-50 p-4 mb-4">
      <div className="flex items-start gap-3">
        <AlertTriangle className="text-amber-600 mt-0.5" size={20} />
        <div>
          <p className="font-semibold text-amber-900">Drift threshold crossed</p>
          <p className="text-sm text-amber-800">{alert.message}</p>
          <p className="text-xs text-amber-600 mt-1">
            Detected on {new Date(alert.detected_at).toLocaleString()}
          </p>
        </div>
      </div>
      <button
        onClick={onViewDetails}
        className="border border-amber-400 text-amber-800 rounded-lg px-3 py-1.5 text-sm font-medium hover:bg-amber-100"
      >
        View Drift Details
      </button>
    </div>
  );
}
