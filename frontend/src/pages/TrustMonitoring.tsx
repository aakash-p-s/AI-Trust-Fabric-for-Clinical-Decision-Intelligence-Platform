import { useEffect, useState } from "react";
import ConfidenceTrendChart from "../components/charts/ConfidenceTrendChart";
import FlagRateTrendChart from "../components/charts/FlagRateTrendChart";
import DriftAlertBanner from "../components/ui/DriftAlertBanner";
import MetricCard from "../components/ui/MetricCard";
import StatusBadge from "../components/ui/StatusBadge";
import { getDriftAlerts, getRulebook, getTrustMonitoringSummary, runTrustCheckNow } from "../lib/api";
import type { DriftAlert, TrustMonitoringSummary } from "../lib/types";
import { formatConfidence } from "../lib/utils";

export default function TrustMonitoring() {
  const [summary, setSummary] = useState<TrustMonitoringSummary | null>(null);
  const [alerts, setAlerts] = useState<DriftAlert[]>([]);
  const [threshold, setThreshold] = useState(0.75);
  const [modelVersion, setModelVersion] = useState<string | undefined>(undefined);
  const [running, setRunning] = useState(false);
  const [lastCheck, setLastCheck] = useState<string | null>(null);

  const load = () => {
    getTrustMonitoringSummary(modelVersion).then(setSummary);
    getDriftAlerts().then((r) => setAlerts(r.alerts));
    getRulebook().then((r) => setThreshold(r.minimum_confidence_threshold));
  };

  useEffect(load, [modelVersion]);

  const activeAlert = alerts.find((a) => a.status === "Active");

  const handleRunNow = async () => {
    setRunning(true);
    try {
      const result = await runTrustCheckNow(modelVersion);
      setSummary(result);
      setLastCheck(new Date().toLocaleString());
      const alertsRes = await getDriftAlerts();
      setAlerts(alertsRes.alerts);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <p className="text-xs text-gray-400">Dashboard &gt; Trust Monitoring</p>
      </div>
      <div className="flex items-center gap-2 mb-4">
        <h1 className="text-xl font-semibold">Trust Monitoring</h1>
        <span className="badge-gray">Compliance/Governance only</span>
      </div>

      {activeAlert && (
        <DriftAlertBanner
          alert={activeAlert}
          onViewDetails={() => document.getElementById("drift-alerts-table")?.scrollIntoView({ behavior: "smooth" })}
        />
      )}

      <div className="flex flex-wrap items-center gap-3 mb-4">
        <select
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
          value={modelVersion || ""}
          onChange={(e) => setModelVersion(e.target.value || undefined)}
        >
          <option value="">All Versions</option>
          <option value="v2.0">v2.0</option>
          <option value="v2.1">v2.1</option>
          <option value="v1.9">v1.9</option>
        </select>
        <button
          className="btn-primary ml-auto"
          onClick={handleRunNow}
          disabled={running}
        >
          {running ? "Running..." : "Run trust check now"}
        </button>
      </div>

      {summary && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <ConfidenceTrendChart data={summary.confidence_trend} threshold={threshold} />
            <FlagRateTrendChart data={summary.flag_rate_trend} />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <MetricCard
              label="Avg Confidence (latest)"
              value={formatConfidence(summary.avg_confidence_latest)}
              subtext={`${summary.avg_confidence_delta_pct >= 0 ? "-" : "+"}${Math.abs(
                summary.avg_confidence_delta_pct
              ).toFixed(1)}% vs range start`}
              subtextColor={summary.avg_confidence_delta_pct > 0 ? "red" : "green"}
            />
            <MetricCard
              label="% Flagged (latest)"
              value={`${summary.pct_flagged_latest.toFixed(1)}%`}
              subtext={`${summary.pct_flagged_delta_pp >= 0 ? "+" : ""}${summary.pct_flagged_delta_pp.toFixed(
                1
              )}pp vs range start`}
              subtextColor={summary.pct_flagged_delta_pp > 0 ? "red" : "green"}
            />
            <MetricCard label="Predictions" value={summary.total_predictions_in_range} subtext="Total in range" />
            <div className="card">
              <p className="text-xs uppercase text-gray-500 mb-1">Drift Status</p>
              <StatusBadge status={summary.drift_status} />
              {summary.drift_since && (
                <p className="text-xs text-gray-400 mt-1">
                  Since {new Date(summary.drift_since).toLocaleDateString()}
                </p>
              )}
            </div>
          </div>
        </>
      )}

      <div className="card" id="drift-alerts-table">
        <p className="font-semibold mb-3">Recent Drift Alerts</p>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 border-b border-gray-200">
              <th className="py-2 font-medium">Alert</th>
              <th className="py-2 font-medium">Model / Version</th>
              <th className="py-2 font-medium">Detected On</th>
              <th className="py-2 font-medium">Severity</th>
              <th className="py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((a) => (
              <tr key={a.id} className="border-b border-gray-100">
                <td className="py-2">{a.message}</td>
                <td className="py-2">{a.model_version}</td>
                <td className="py-2 text-gray-500">{new Date(a.detected_at).toLocaleString()}</td>
                <td className="py-2">
                  <StatusBadge status={a.severity} />
                </td>
                <td className="py-2">
                  <StatusBadge status={a.status} />
                </td>
              </tr>
            ))}
            {alerts.length === 0 && (
              <tr>
                <td colSpan={5} className="py-4 text-center text-gray-400">
                  No alerts recorded yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex justify-between text-xs text-gray-400 mt-3">
        <span>Most recent trust check: {lastCheck || "not yet run this session"}</span>
        <span>Auto-checks enabled every 6 hours</span>
      </div>
    </div>
  );
}
