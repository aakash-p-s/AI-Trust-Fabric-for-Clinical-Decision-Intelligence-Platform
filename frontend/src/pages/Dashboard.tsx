// // import { useEffect, useState } from "react";
// // import { useNavigate } from "react-router-dom";
// // import MetricCard from "../components/ui/MetricCard";
// // import StatusBadge from "../components/ui/StatusBadge";
// // import { getDashboardSummary, listTwins, type TwinListParams } from "../lib/api";
// // import type { DashboardSummary, TwinSummary } from "../lib/types";
// // import { formatConfidence } from "../lib/utils";

// // const PAGE_SIZE = 20;

// // export default function Dashboard() {
// //   const navigate = useNavigate();

// //   const [summary, setSummary] = useState<DashboardSummary | null>(null);
// //   const [twins, setTwins] = useState<TwinSummary[]>([]);
// //   const [total, setTotal] = useState(0);
// //   const [page, setPage] = useState(1);

// //   const [status, setStatus] = useState<TwinListParams["status"]>("all");
// //   const [modelVersion, setModelVersion] = useState("");
// //   const [search, setSearch] = useState("");
// //   const [sortBy, setSortBy] = useState<TwinListParams["sort_by"]>("twin_created_at");
// //   const [sortDir, setSortDir] = useState<TwinListParams["sort_dir"]>("desc");

// //   useEffect(() => {
// //     getDashboardSummary().then(setSummary).catch(() => {});
// //   }, [twins]);

// //   useEffect(() => {
// //     listTwins({
// //       status,
// //       model_version: modelVersion || undefined,
// //       search: search || undefined,
// //       sort_by: sortBy,
// //       sort_dir: sortDir,
// //       page,
// //       limit: PAGE_SIZE,
// //     })
// //       .then((res) => {
// //         setTwins(res.twins);
// //         setTotal(res.total);
// //       })
// //       .catch(() => {});
// //   }, [status, modelVersion, search, sortBy, sortDir, page]);

// //   const toggleSort = (field: NonNullable<TwinListParams["sort_by"]>) => {
// //     if (sortBy === field) {
// //       setSortDir(sortDir === "asc" ? "desc" : "asc");
// //     } else {
// //       setSortBy(field);
// //       setSortDir("desc");
// //     }
// //   };

// //   const resetFilters = () => {
// //     setStatus("all");
// //     setModelVersion("");
// //     setSearch("");
// //     setPage(1);
// //   };

// //   const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
// //   const rangeStart = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
// //   const rangeEnd = Math.min(page * PAGE_SIZE, total);

// //   return (
// //     <div>
// //       <h1 className="text-xl font-semibold mb-4">Dashboard</h1>

// //       <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
// //         <MetricCard label="Total Predictions" value={summary?.total_predictions ?? "-"} subtext="All time" />
// //         <MetricCard
// //           label="Flagged Count"
// //           value={summary?.flagged_count ?? "-"}
// //           subtext={summary ? `${summary.flagged_pct}% of total` : undefined}
// //           subtextColor="red"
// //         />
// //         <MetricCard
// //           label="Avg Confidence"
// //           value={summary ? formatConfidence(summary.avg_confidence) : "-"}
// //           subtext="Across all predictions"
// //         />
// //         <MetricCard
// //           label="Drift Alerts"
// //           value={summary?.active_drift_alerts ?? "-"}
// //           subtext="Active alerts"
// //           subtextColor={summary && summary.active_drift_alerts > 0 ? "red" : "gray"}
// //         />
// //       </div>

// //       <div className="flex flex-wrap gap-3 items-center mb-4">
// //         <select
// //           className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
// //           value={status}
// //           onChange={(e) => {
// //             setStatus(e.target.value as TwinListParams["status"]);
// //             setPage(1);
// //           }}
// //         >
// //           <option value="all">All Statuses</option>
// //           <option value="cleared">Cleared</option>
// //           <option value="flagged">Flagged</option>
// //         </select>
// //         <select
// //           className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
// //           value={modelVersion}
// //           onChange={(e) => {
// //             setModelVersion(e.target.value);
// //             setPage(1);
// //           }}
// //         >
// //           <option value="">All Versions</option>
// //           <option value="v2.0">v2.0</option>
// //           <option value="v2.1">v2.1</option>
// //           <option value="v1.9">v1.9</option>
// //         </select>
// //         <input
// //           className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
// //           placeholder="Search by Patient ID..."
// //           value={search}
// //           onChange={(e) => {
// //             setSearch(e.target.value);
// //             setPage(1);
// //           }}
// //         />
// //         <button onClick={resetFilters} className="text-sm text-gray-500 hover:text-gray-800 ml-auto">
// //           Reset Filters
// //         </button>
// //       </div>

// //       <div className="card p-0 overflow-hidden">
// //         <table className="w-full text-sm">
// //           <thead>
// //             <tr className="text-left text-gray-500 border-b border-gray-200 bg-gray-50">
// //               <th className="py-2 px-4 cursor-pointer" onClick={() => toggleSort("twin_created_at")}>
// //                 Patient ID
// //               </th>
// //               <th className="py-2 px-4">Model + Version</th>
// //               <th className="py-2 px-4">Prediction</th>
// //               <th className="py-2 px-4 cursor-pointer" onClick={() => toggleSort("confidence")}>
// //                 Confidence
// //               </th>
// //               <th className="py-2 px-4">Status</th>
// //               <th className="py-2 px-4">Action</th>
// //             </tr>
// //           </thead>
// //           <tbody>
// //             {twins.map((t) => (
// //               <tr key={t.twin_id} className="border-b border-gray-100">
// //                 <td className="py-2 px-4">{t.patient_id}</td>
// //                 <td className="py-2 px-4">{t.prediction.model_version}</td>
// //                 <td className="py-2 px-4">{t.prediction.label}</td>
// //                 <td className="py-2 px-4">{formatConfidence(t.prediction.confidence)}</td>
// //                 <td className="py-2 px-4">
// //                   <StatusBadge status={t.flagged ? "Flagged" : "Cleared"} />
// //                 </td>
// //                 <td className="py-2 px-4">
// //                   <button
// //                     className="border border-gray-300 rounded-md px-3 py-1 text-xs font-medium hover:bg-gray-50"
// //                     onClick={() => navigate(`/twins/${t.twin_id}`)}
// //                   >
// //                     {t.flagged ? "Review" : "View"}
// //                   </button>
// //                 </td>
// //               </tr>
// //             ))}
// //             {twins.length === 0 && (
// //               <tr>
// //                 <td colSpan={6} className="py-6 text-center text-gray-400">
// //                   No predictions match the current filters.
// //                 </td>
// //               </tr>
// //             )}
// //           </tbody>
// //         </table>
// //         <div className="flex items-center justify-between px-4 py-3 text-xs text-gray-500">
// //           <span>
// //             Showing {rangeStart} to {rangeEnd} of {total} results
// //           </span>
// //           <div className="flex gap-1">
// //             <button
// //               disabled={page <= 1}
// //               onClick={() => setPage((p) => Math.max(1, p - 1))}
// //               className="px-2 py-1 border border-gray-200 rounded disabled:opacity-40"
// //             >
// //               Prev
// //             </button>
// //             <span className="px-2 py-1">
// //               {page} / {totalPages}
// //             </span>
// //             <button
// //               disabled={page >= totalPages}
// //               onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
// //               className="px-2 py-1 border border-gray-200 rounded disabled:opacity-40"
// //             >
// //               Next
// //             </button>
// //           </div>
// //         </div>
// //       </div>
// //     </div>
// //   );
// // }
// import { useEffect, useRef, useState } from "react";
// import { useNavigate } from "react-router-dom";
// import MetricCard from "../components/ui/MetricCard";
// import StatusBadge from "../components/ui/StatusBadge";
// import { getDashboardSummary, listTwins, type TwinListParams } from "../lib/api";
// import type { DashboardSummary, TwinSummary } from "../lib/types";
// import { formatConfidence } from "../lib/utils";

// const PAGE_SIZE = 20;
// const LIVE_REFRESH_INTERVAL_MS = 5000;

// export default function Dashboard() {
//   const navigate = useNavigate();

//   const [summary, setSummary] = useState<DashboardSummary | null>(null);
//   const [twins, setTwins] = useState<TwinSummary[]>([]);
//   const [total, setTotal] = useState(0);
//   const [page, setPage] = useState(1);

//   const [status, setStatus] = useState<TwinListParams["status"]>("all");
//   const [modelVersion, setModelVersion] = useState("");
//   const [search, setSearch] = useState("");
//   const [sortBy, setSortBy] = useState<TwinListParams["sort_by"]>("twin_created_at");
//   const [sortDir, setSortDir] = useState<TwinListParams["sort_dir"]>("desc");

//   const [liveMode, setLiveMode] = useState(true);
//   const liveModeRef = useRef(liveMode);
//   liveModeRef.current = liveMode;

//   useEffect(() => {
//     const fetchAll = () => {
//       getDashboardSummary().then(setSummary).catch(() => {});
//       listTwins({
//         status,
//         model_version: modelVersion || undefined,
//         search: search || undefined,
//         sort_by: sortBy,
//         sort_dir: sortDir,
//         page,
//         limit: PAGE_SIZE,
//       })
//         .then((res) => {
//           setTwins(res.twins);
//           setTotal(res.total);
//         })
//         .catch(() => {});
//     };

//     fetchAll(); // always fetch once immediately on mount / filter change

//     const interval = setInterval(() => {
//       if (liveModeRef.current) fetchAll();
//     }, LIVE_REFRESH_INTERVAL_MS);

//     return () => clearInterval(interval);
//   }, [status, modelVersion, search, sortBy, sortDir, page]);

//   const toggleSort = (field: NonNullable<TwinListParams["sort_by"]>) => {
//     if (sortBy === field) {
//       setSortDir(sortDir === "asc" ? "desc" : "asc");
//     } else {
//       setSortBy(field);
//       setSortDir("desc");
//     }
//   };

//   const resetFilters = () => {
//     setStatus("all");
//     setModelVersion("");
//     setSearch("");
//     setPage(1);
//   };

//   const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
//   const rangeStart = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
//   const rangeEnd = Math.min(page * PAGE_SIZE, total);

//   return (
//     <div>
//       <div className="flex items-center gap-3 mb-4">
//         <h1 className="text-xl font-semibold">Dashboard</h1>
//         <button
//           onClick={() => setLiveMode((v) => !v)}
//           className={`flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full border ${
//             liveMode
//               ? "border-green-300 bg-green-50 text-green-700"
//               : "border-gray-300 bg-gray-50 text-gray-500"
//           }`}
//         >
//           <span
//             className={`w-1.5 h-1.5 rounded-full ${liveMode ? "bg-green-500 animate-pulse" : "bg-gray-400"}`}
//           />
//           {liveMode ? "Live" : "Paused"}
//         </button>
//       </div>

//       <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
//         <MetricCard label="Total Predictions" value={summary?.total_predictions ?? "-"} subtext="All time" />
//         <MetricCard
//           label="Flagged Count"
//           value={summary?.flagged_count ?? "-"}
//           subtext={summary ? `${summary.flagged_pct}% of total` : undefined}
//           subtextColor="red"
//         />
//         <MetricCard
//           label="Avg Confidence"
//           value={summary ? formatConfidence(summary.avg_confidence) : "-"}
//           subtext="Across all predictions"
//         />
//         <MetricCard
//           label="Drift Alerts"
//           value={summary?.active_drift_alerts ?? "-"}
//           subtext="Active alerts"
//           subtextColor={summary && summary.active_drift_alerts > 0 ? "red" : "gray"}
//         />
//       </div>

//       <div className="flex flex-wrap gap-3 items-center mb-4">
//         <select
//           className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
//           value={status}
//           onChange={(e) => {
//             setStatus(e.target.value as TwinListParams["status"]);
//             setPage(1);
//           }}
//         >
//           <option value="all">All Statuses</option>
//           <option value="cleared">Cleared</option>
//           <option value="flagged">Flagged</option>
//         </select>
//         <select
//           className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
//           value={modelVersion}
//           onChange={(e) => {
//             setModelVersion(e.target.value);
//             setPage(1);
//           }}
//         >
//           <option value="">All Versions</option>
//           <option value="v2.0">v2.0</option>
//           <option value="v2.1">v2.1</option>
//           <option value="v1.9">v1.9</option>
//         </select>
//         <input
//           className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
//           placeholder="Search by Patient ID..."
//           value={search}
//           onChange={(e) => {
//             setSearch(e.target.value);
//             setPage(1);
//           }}
//         />
//         <button onClick={resetFilters} className="text-sm text-gray-500 hover:text-gray-800 ml-auto">
//           Reset Filters
//         </button>
//       </div>

//       <div className="card p-0 overflow-hidden">
//         <table className="w-full text-sm">
//           <thead>
//             <tr className="text-left text-gray-500 border-b border-gray-200 bg-gray-50">
//               <th className="py-2 px-4 cursor-pointer" onClick={() => toggleSort("twin_created_at")}>
//                 Patient ID
//               </th>
//               <th className="py-2 px-4">Model + Version</th>
//               <th className="py-2 px-4">Prediction</th>
//               <th className="py-2 px-4 cursor-pointer" onClick={() => toggleSort("confidence")}>
//                 Confidence
//               </th>
//               <th className="py-2 px-4">Status</th>
//               <th className="py-2 px-4">Action</th>
//             </tr>
//           </thead>
//           <tbody>
//             {twins.map((t) => (
//               <tr key={t.twin_id} className="border-b border-gray-100">
//                 <td className="py-2 px-4">{t.patient_id}</td>
//                 <td className="py-2 px-4">{t.prediction.model_version}</td>
//                 <td className="py-2 px-4">{t.prediction.label}</td>
//                 <td className="py-2 px-4">{formatConfidence(t.prediction.confidence)}</td>
//                 <td className="py-2 px-4">
//                   <StatusBadge status={t.flagged ? "Flagged" : "Cleared"} />
//                 </td>
//                 <td className="py-2 px-4">
//                   <button
//                     className="border border-gray-300 rounded-md px-3 py-1 text-xs font-medium hover:bg-gray-50"
//                     onClick={() => navigate(`/twins/${t.twin_id}`)}
//                   >
//                     {t.flagged ? "Review" : "View"}
//                   </button>
//                 </td>
//               </tr>
//             ))}
//             {twins.length === 0 && (
//               <tr>
//                 <td colSpan={6} className="py-6 text-center text-gray-400">
//                   No predictions match the current filters.
//                 </td>
//               </tr>
//             )}
//           </tbody>
//         </table>
//         <div className="flex items-center justify-between px-4 py-3 text-xs text-gray-500">
//           <span>
//             Showing {rangeStart} to {rangeEnd} of {total} results
//           </span>
//           <div className="flex gap-1">
//             <button
//               disabled={page <= 1}
//               onClick={() => setPage((p) => Math.max(1, p - 1))}
//               className="px-2 py-1 border border-gray-200 rounded disabled:opacity-40"
//             >
//               Prev
//             </button>
//             <span className="px-2 py-1">
//               {page} / {totalPages}
//             </span>
//             <button
//               disabled={page >= totalPages}
//               onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
//               className="px-2 py-1 border border-gray-200 rounded disabled:opacity-40"
//             >
//               Next
//             </button>
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// }
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import MetricCard from "../components/ui/MetricCard";
import NowProcessingPanel from "../components/ui/NowProcessingPanel";
import StatusBadge from "../components/ui/StatusBadge";
import { getDashboardSummary, listTwins, type TwinListParams } from "../lib/api";
import type { DashboardSummary, TwinSummary } from "../lib/types";
import { formatConfidence } from "../lib/utils";

const PAGE_SIZE = 20;
const LIVE_REFRESH_INTERVAL_MS = 5000;

function twinStatus(t: TwinSummary): "Cleared" | "Pending Review" | "Approved" | "Overridden" {
  if (!t.flagged) return "Cleared";
  if (!t.review) return "Pending Review";
  return t.review.decision === "approve" ? "Approved" : "Overridden";
}

export default function Dashboard() {
  const navigate = useNavigate();

  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [twins, setTwins] = useState<TwinSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);

  const [status, setStatus] = useState<TwinListParams["status"]>("all");
  const [modelVersion, setModelVersion] = useState("");
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<TwinListParams["sort_by"]>("twin_created_at");
  const [sortDir, setSortDir] = useState<TwinListParams["sort_dir"]>("desc");

  const [liveMode, setLiveMode] = useState(true);
  const liveModeRef = useRef(liveMode);
  liveModeRef.current = liveMode;

  const fetchAllRef = useRef<() => void>(() => {});

  useEffect(() => {
    const fetchAll = () => {
      getDashboardSummary().then(setSummary).catch(() => {});
      listTwins({
        status,
        model_version: modelVersion || undefined,
        search: search || undefined,
        sort_by: sortBy,
        sort_dir: sortDir,
        page,
        limit: PAGE_SIZE,
      })
        .then((res) => {
          setTwins(res.twins);
          setTotal(res.total);
        })
        .catch(() => {});
    };
    fetchAllRef.current = fetchAll;

    fetchAll(); // always fetch once immediately on mount / filter change

    const interval = setInterval(() => {
      if (liveModeRef.current) fetchAll();
    }, LIVE_REFRESH_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [status, modelVersion, search, sortBy, sortDir, page]);

  const toggleSort = (field: NonNullable<TwinListParams["sort_by"]>) => {
    if (sortBy === field) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortDir("desc");
    }
  };

  const resetFilters = () => {
    setStatus("all");
    setModelVersion("");
    setSearch("");
    setPage(1);
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const rangeStart = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const rangeEnd = Math.min(page * PAGE_SIZE, total);

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <button
          onClick={() => setLiveMode((v) => !v)}
          className={`flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full border ${
            liveMode
              ? "border-green-300 bg-green-50 text-green-700"
              : "border-gray-300 bg-gray-50 text-gray-500"
          }`}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${liveMode ? "bg-green-500 animate-pulse" : "bg-gray-400"}`}
          />
          {liveMode ? "Live" : "Paused"}
        </button>
      </div>

      <NowProcessingPanel onPatientDone={() => fetchAllRef.current()} />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <MetricCard label="Total Predictions" value={summary?.total_predictions ?? "-"} subtext="All time" />
        <MetricCard
          label="Flagged Count"
          value={summary?.flagged_count ?? "-"}
          subtext={summary ? `${summary.flagged_pct}% of total` : undefined}
          subtextColor="red"
        />
        <MetricCard
          label="Avg Confidence"
          value={summary ? formatConfidence(summary.avg_confidence) : "-"}
          subtext="Across all predictions"
        />
        <MetricCard
          label="Drift Alerts"
          value={summary?.active_drift_alerts ?? "-"}
          subtext="Active alerts"
          subtextColor={summary && summary.active_drift_alerts > 0 ? "red" : "gray"}
        />
      </div>

      <div className="flex flex-wrap gap-3 items-center mb-4">
        <select
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
          value={status}
          onChange={(e) => {
            setStatus(e.target.value as TwinListParams["status"]);
            setPage(1);
          }}
        >
          <option value="all">All Statuses</option>
          <option value="cleared">Cleared</option>
          <option value="flagged">Flagged</option>
        </select>
        <select
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
          value={modelVersion}
          onChange={(e) => {
            setModelVersion(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All Versions</option>
          <option value="v2.0">v2.0</option>
          <option value="v2.1">v2.1</option>
          <option value="v1.9">v1.9</option>
        </select>
        <input
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
          placeholder="Search by Patient ID..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
        <button onClick={resetFilters} className="text-sm text-gray-500 hover:text-gray-800 ml-auto">
          Reset Filters
        </button>
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 border-b border-gray-200 bg-gray-50">
              <th className="py-2 px-4 cursor-pointer" onClick={() => toggleSort("twin_created_at")}>
                Patient ID
              </th>
              <th className="py-2 px-4">Model + Version</th>
              <th className="py-2 px-4">Prediction</th>
              <th className="py-2 px-4 cursor-pointer" onClick={() => toggleSort("confidence")}>
                Confidence
              </th>
              <th className="py-2 px-4">Status</th>
              <th className="py-2 px-4">Action</th>
            </tr>
          </thead>
          <tbody>
            {twins.map((t) => (
              <tr key={t.twin_id} className="border-b border-gray-100">
                <td className="py-2 px-4">{t.patient_id}</td>
                <td className="py-2 px-4">{t.prediction.model_version}</td>
                <td className="py-2 px-4">{t.prediction.label}</td>
                <td className="py-2 px-4">{formatConfidence(t.prediction.confidence)}</td>
                <td className="py-2 px-4">
                  <StatusBadge status={twinStatus(t)} />
                </td>
                <td className="py-2 px-4">
                  <button
                    className="border border-gray-300 rounded-md px-3 py-1 text-xs font-medium hover:bg-gray-50"
                    onClick={() => navigate(`/twins/${t.twin_id}`)}
                  >
                    {t.flagged && !t.review ? "Review" : "View"}
                  </button>
                </td>
              </tr>
            ))}
            {twins.length === 0 && (
              <tr>
                <td colSpan={6} className="py-6 text-center text-gray-400">
                  No predictions match the current filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
        <div className="flex items-center justify-between px-4 py-3 text-xs text-gray-500">
          <span>
            Showing {rangeStart} to {rangeEnd} of {total} results
          </span>
          <div className="flex gap-1">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="px-2 py-1 border border-gray-200 rounded disabled:opacity-40"
            >
              Prev
            </button>
            <span className="px-2 py-1">
              {page} / {totalPages}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              className="px-2 py-1 border border-gray-200 rounded disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
