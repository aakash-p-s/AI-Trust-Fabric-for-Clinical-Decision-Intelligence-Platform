import { AlertTriangle, ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import ReviewActionPanel from "../components/ui/ReviewActionPanel";
import { useAuth } from "../contexts/AuthContext";
import { getTwin, reviewTwin } from "../lib/api";
import type { DigitalTwinDetail } from "../lib/types";
import { formatConfidence, formatRelativeTime } from "../lib/utils";

export default function TwinDetail() {
  const { twinId } = useParams<{ twinId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [twin, setTwin] = useState<DigitalTwinDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    if (!twinId) return;
    getTwin(twinId).then(setTwin).catch((e) => setError(e.message));
  };

  useEffect(load, [twinId]);

  if (error) return <p className="text-red-600">{error}</p>;
  if (!twin) return <p className="text-gray-400">Loading...</p>;

  const isGovernance = user?.role === "compliance_governance";
  const canReview = isGovernance && twin.flagged && !twin.review;

  const handleApprove = async (notes: string) => {
    if (!user) return;
    await reviewTwin(twin.twin_id, user.username, "approve", notes, user.role);
    load();
  };

  const handleOverride = async (notes: string) => {
    if (!user) return;
    await reviewTwin(twin.twin_id, user.username, "override", notes, user.role);
    load();
  };

  const complianceRows = [
    { label: "Model Version Approved", value: twin.compliance.model_version_approved },
    { label: "Confidence Threshold Met", value: twin.compliance.confidence_ok },
    {
      label: "High-Risk Condition Review",
      value: twin.compliance.high_risk_requires_review,
      customText: twin.compliance.high_risk_requires_review ? "Required" : "Not Required",
    },
  ];

  return (
    <div>
      <button
        onClick={() => navigate("/dashboard")}
        className="flex items-center gap-1 text-sm text-blue-600 mb-3"
      >
        <ArrowLeft size={14} /> Back to Dashboard
      </button>
      <h1 className="text-xl font-semibold mb-4">Twin Detail</h1>

      <div className="card mb-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-xs text-gray-500 mb-1">Prediction</p>
            <p className="font-semibold flex items-center gap-1">
              {twin.flagged && <AlertTriangle size={14} className="text-amber-500" />}
              {twin.prediction.label}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Confidence</p>
            <p className="font-semibold">{formatConfidence(twin.prediction.confidence)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Model + Version</p>
            <p className="font-semibold">{twin.prediction.model_version}</p>
            <p className="text-xs text-gray-400">{twin.lineage.source}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Time Generated</p>
            <p className="font-semibold">{new Date(twin.twin_created_at).toLocaleString()}</p>
            <p className="text-xs text-gray-400">({formatRelativeTime(twin.twin_created_at)})</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* 1. Lineage */}
        <div className="card">
          <p className="font-semibold mb-2">1. Lineage</p>
          <p className="text-xs text-gray-500">Input Source</p>
          <p className="text-sm mb-2">{twin.lineage.source}</p>
          <p className="text-xs text-gray-500">Data Capture Time</p>
          <p className="text-sm mb-2">{new Date(twin.lineage.input_captured_at).toLocaleString()}</p>
          <p className="text-xs text-gray-500">Data Pipeline</p>
          <p className="text-sm mb-2">Ingestion &rarr; Validation &rarr; Model Inference</p>
          <p className="text-xs text-gray-500">Data Snapshot ID</p>
          <p className="text-xs font-mono break-all">{twin.twin_id}</p>
        </div>

        {/* 2. Explanation */}
        <div className="card">
          <p className="font-semibold mb-2">2. Explanation</p>
          <span className="badge-gray inline-block mb-2">AI-generated narrative</span>
          <p className="text-sm text-gray-700 mb-2">{twin.explanation}</p>
          {twin.grounded_in_sources.length > 0 && (
            <p className="text-xs text-gray-400">
              Grounded in: {twin.grounded_in_sources.map((s) => s.source).join(", ")}
            </p>
          )}
          {twin.low_grounding_confidence && (
            <p className="text-xs text-amber-600 mt-1">
              This explanation has lower supporting evidence than usual.
            </p>
          )}
        </div>

        {/* 3. Compliance */}
        <div className="card">
          <p className="font-semibold mb-2">3. Compliance</p>
          <table className="w-full text-sm">
            <tbody>
              {complianceRows.map((row) => (
                <tr key={row.label} className="border-b border-gray-100">
                  <td className="py-1.5 text-gray-600">{row.label}</td>
                  <td className="py-1.5 text-right">
                    {row.customText ? (
                      <span className={row.value ? "text-amber-600" : "text-gray-400"}>{row.customText}</span>
                    ) : (
                      <span className={row.value ? "text-green-600" : "text-red-600"}>
                        {row.value ? "Pass" : "Fail"}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
              <tr>
                <td className="py-1.5 font-medium">Overall Status</td>
                <td className="py-1.5 text-right">
                  <StatusText flagged={twin.flagged} />
                </td>
              </tr>
            </tbody>
          </table>
          {twin.flagged && twin.compliance.flag_reasons.length > 0 && (
            <ul className="text-xs text-gray-500 list-disc list-inside mt-2">
              {twin.compliance.flag_reasons.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          )}
        </div>

        {/* 4. Patient Context */}
        <div className="card">
          <p className="font-semibold mb-2">4. Patient Context</p>
          <p className="text-xs text-gray-500">Patient ID</p>
          <p className="text-sm mb-2">{twin.patient.patient_id}</p>
          <p className="text-xs text-gray-500">Age</p>
          <p className="text-sm mb-2">{twin.patient.age}</p>
          <p className="text-xs text-gray-500">Primary Symptoms</p>
          <p className="text-sm mb-2">{twin.patient.symptoms.join(", ")}</p>
          <p className="text-xs text-gray-500">Relevant History</p>
          <p className="text-sm mb-2">{twin.patient.relevant_history}</p>
          <p className="text-xs text-gray-500">Scan Type</p>
          <p className="text-sm">{twin.patient.scan_type}</p>
        </div>
      </div>

      {canReview && <ReviewActionPanel onApprove={handleApprove} onOverride={handleOverride} />}

      {twin.review && (
        <p className="text-xs text-gray-400 mt-4">
          Reviewed by {twin.review.reviewed_by} on {new Date(twin.review.reviewed_at).toLocaleString()} --{" "}
          {twin.review.decision}
          {twin.review.notes ? `: "${twin.review.notes}"` : ""}
        </p>
      )}

      {!isGovernance && (
        <p className="text-xs text-gray-400 mt-4">
          Viewed by {user?.display_name} on {new Date().toLocaleString()}
        </p>
      )}
    </div>
  );
}

function StatusText({ flagged }: { flagged: boolean }) {
  return flagged ? (
    <span className="text-amber-600 font-medium">Flagged for Review</span>
  ) : (
    <span className="text-green-600 font-medium">Cleared</span>
  );
}
