import { Fragment, useEffect, useState } from "react";
import MetricCard from "../components/ui/MetricCard";
import { getGovernanceSummary, getPatientProcessingLog } from "../lib/api";
import type { GovernanceSummary, PatientProcessingLogEntry } from "../lib/types";

const LANGSMITH_PROJECT_URL =
  "https://smith.langchain.com/o/b0853474-0532-4dc5-9077-5b14d6bf9aa1/projects/p/890e5e17-90ad-4e54-8a08-5c7161802383";

const EXPLAINABILITY_BADGE: Record<string, { label: (modelUsed: string | null) => string; className: string }> = {
  primary_llm: { label: (m) => shortModelName(m), className: "badge-green" },
  fallback_llm: { label: (m) => `${shortModelName(m)} (fallback)`, className: "badge-amber" },
  deterministic_fallback: { label: () => "deterministic fallback", className: "badge-red" },
};

const RAG_DOT: Record<string, string> = {
  live: "bg-green-500",
  degraded: "bg-amber-500",
  unavailable: "bg-red-500",
};

const RAG_TEXT: Record<string, string> = {
  live: "text-green-700",
  degraded: "text-amber-700",
  unavailable: "text-red-700",
};

function shortModelName(model: string | null): string {
  if (!model) return "unknown";
  const withoutOrg = model.split("/").pop() || model;
  return withoutOrg.replace(":free", "");
}

function formatSeconds(ms: number): string {
  return `${(ms / 1000).toFixed(1)}s`;
}

function reviewLabel(entry: PatientProcessingLogEntry): { text: string; className: string } {
  if (!entry.flagged) return { text: "Not Required", className: "badge-gray" };
  if (!entry.review) return { text: "Pending", className: "badge-amber" };
  if (entry.review.decision === "approve") return { text: "Approved", className: "badge-green" };
  return { text: "Overridden", className: "badge-gray" };
}

export default function Governance() {
  const [summary, setSummary] = useState<GovernanceSummary | null>(null);
  const [entries, setEntries] = useState<PatientProcessingLogEntry[]>([]);
  const [expandedTwinId, setExpandedTwinId] = useState<string | null>(null);

  useEffect(() => {
    const fetchAll = () => {
      getGovernanceSummary().then(setSummary).catch(() => {});
      getPatientProcessingLog().then((res) => setEntries(res.entries)).catch(() => {});
    };
    fetchAll();
    const interval = setInterval(fetchAll, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">Governance</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <MetricCard label="Total Processed" value={summary?.total_processed ?? "-"} subtext="All predictions" />
        <MetricCard label="Avg Total Time" value={summary ? formatSeconds(summary.avg_total_time_ms) : "-"} />
        <MetricCard label="Avg Explainability" value={summary ? formatSeconds(summary.avg_explainability_ms) : "-"} />
        <div className="card">
          <p className="text-xs uppercase text-gray-500 mb-1">Total Tokens</p>
          <p className="text-2xl font-semibold">{summary?.total_tokens?.toLocaleString() ?? "-"}</p>
          <a
            href={LANGSMITH_PROJECT_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[11px] text-blue-600 hover:underline mt-1 inline-block"
          >
            View more
          </a>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <MetricCard
          label="RAG Live Rate"
          value={summary ? `${summary.rag_live_rate_pct}%` : "-"}
          subtext="Successful retrievals"
          subtextColor="green"
        />
        <MetricCard
          label="Fallback Rate"
          value={summary ? `${summary.fallback_rate_pct}%` : "-"}
          subtext="Nemotron fallback usage"
          subtextColor={summary && summary.fallback_rate_pct > 0 ? "red" : "gray"}
        />
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 border-b border-gray-200 bg-gray-50">
              <th className="py-2 px-4">Patient</th>
              <th className="py-2 px-4">Pipeline Stages</th>
              <th className="py-2 px-4">RAG</th>
              <th className="py-2 px-4">Explainability</th>
              <th className="py-2 px-4">Total</th>
              <th className="py-2 px-4">Review</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => {
              const isExpanded = expandedTwinId === entry.twin_id;
              const cascade = entry.explanation_cascade;
              const rag = entry.rag_details;
              const review = reviewLabel(entry);
              const badge = cascade ? EXPLAINABILITY_BADGE[cascade.final_source] : null;

              return (
                <Fragment key={entry.twin_id}>
                  <tr
                    className={`border-b border-gray-100 cursor-pointer ${isExpanded ? "bg-blue-50/40" : ""}`}
                    onClick={() => setExpandedTwinId(isExpanded ? null : entry.twin_id)}
                  >
                    <td className="py-2 px-4 font-medium">
                      <span className={isExpanded ? "text-blue-600" : ""}>{entry.patient_id}</span>
                    </td>
                    <td className="py-2 px-4 text-xs text-gray-500">
                      {Object.entries(entry.stage_durations_ms)
                        .filter(([stage]) => stage !== "explainability")
                        .map(([stage, ms]) => `${stage[0].toUpperCase() + stage.slice(1)} ${ms}ms`)
                        .join(" · ")}
                    </td>
                    <td className="py-2 px-4">
                      {rag && (
                        <span className="inline-flex items-center gap-1.5">
                          <span className={`w-1.5 h-1.5 rounded-full ${RAG_DOT[rag.status]}`} />
                          <span className={`text-xs capitalize ${RAG_TEXT[rag.status]}`}>{rag.status}</span>
                        </span>
                      )}
                    </td>
                    <td className="py-2 px-4">
                      {badge && cascade && (
                        <span className="inline-flex items-center gap-2">
                          <span className={badge.className}>{badge.label(cascade.model_used)}</span>
                          <span className="text-xs text-gray-500">
                            {formatSeconds(cascade.duration_ms)}
                            {cascade.token_usage ? ` · ${cascade.token_usage.total_tokens} tok` : " · 0 tok"}
                          </span>
                        </span>
                      )}
                    </td>
                    <td className="py-2 px-4">{formatSeconds(entry.total_duration_ms)}</td>
                    <td className="py-2 px-4">
                      <span className={review.className}>{review.text}</span>
                    </td>
                  </tr>

                  {isExpanded && cascade && (
                    <tr>
                      <td colSpan={6} className="p-4 bg-blue-50/20 border-b border-gray-100">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <p className="font-semibold text-sm mb-2 flex items-center gap-2">
                              {entry.patient_id} — Explainability Cascade
                              <span className="badge-gray">{cascade.attempts.length} attempts</span>
                            </p>
                            <div className="space-y-2">
                              {cascade.attempts.map((attempt, i) => {
                                const succeeded = attempt.status === "success";
                                return (
                                  <div
                                    key={i}
                                    className={`rounded-lg border p-3 text-sm ${
                                      succeeded ? "border-green-200 bg-green-50/50" : "border-red-200 bg-red-50/50"
                                    }`}
                                  >
                                    <div className="flex items-center justify-between mb-1">
                                      <span className="font-mono text-xs">{attempt.model}</span>
                                      <span className={succeeded ? "badge-green" : "badge-red"}>
                                        {succeeded ? "Success" : "Failed"}
                                      </span>
                                    </div>
                                    <p className="text-xs text-gray-600">
                                      {succeeded
                                        ? `${formatSeconds(cascade.duration_ms)} · ${cascade.token_usage?.total_tokens ?? 0} tokens`
                                        : attempt.reason}
                                    </p>
                                  </div>
                                );
                              })}
                            </div>
                          </div>

                          <div className="space-y-3">
                            <div className="card">
                              <p className="font-semibold text-sm mb-2">RAG Details</p>
                              {rag && (
                                <>
                                  <div className="flex items-center gap-1.5 mb-2">
                                    <span className={`w-1.5 h-1.5 rounded-full ${RAG_DOT[rag.status]}`} />
                                    <span className={`text-xs capitalize ${RAG_TEXT[rag.status]}`}>{rag.status}</span>
                                  </div>
                                  <p className="text-xs text-gray-500">
                                    Retrieved facts: {rag.chunks_found} relevant chunks found
                                  </p>
                                  <p className="text-xs text-gray-500">
                                    Top similarity: {rag.top_similarity_score}
                                    {rag.status !== "live" ? " (below threshold)" : ""}
                                  </p>
                                  {rag.error && <p className="text-xs text-red-600 mt-1">{rag.error}</p>}
                                </>
                              )}
                            </div>
                            <div className="card">
                              <p className="font-semibold text-sm mb-1">Impact</p>
                              <p className="text-xs text-gray-500">
                                {rag?.status === "live"
                                  ? "Explanation fully grounded in retrieved evidence."
                                  : rag?.status === "degraded"
                                  ? "Explanation generated with partial grounding."
                                  : "Explanation generated without grounding facts."}
                              </p>
                            </div>
                            <div className="card">
                              <p className="font-semibold text-sm mb-2 flex items-center gap-2">
                                Human Review
                                <span className={review.className}>{review.text}</span>
                              </p>
                              {entry.review ? (
                                <>
                                  <p className="text-xs text-gray-500">
                                    Reviewed by <span className="font-medium">{entry.review.reviewed_by}</span> on{" "}
                                    {new Date(entry.review.reviewed_at).toLocaleString()}
                                  </p>
                                  {entry.review.notes && (
                                    <p className="text-xs text-gray-500 mt-1">"{entry.review.notes}"</p>
                                  )}
                                </>
                              ) : (
                                <p className="text-xs text-gray-500">
                                  {entry.flagged
                                    ? "Awaiting Compliance/Governance review."
                                    : "No review required for this prediction."}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
            {entries.length === 0 && (
              <tr>
                <td colSpan={6} className="py-6 text-center text-gray-400">
                  No predictions processed yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
