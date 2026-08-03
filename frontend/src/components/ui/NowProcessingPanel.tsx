import { useEffect, useRef, useState } from "react";
import { getActivePredictionStream } from "../../lib/api";
import PipelineProgress from "./PipelineProgress";

const POLL_INTERVAL_MS = 500;
// Keep showing the final "Cleared/Flagged" result for a moment after
// completion, instead of the panel vanishing the instant done=true fires.
const LINGER_AFTER_DONE_MS = 3000;

interface ActiveStatus {
  request_id: string;
  patient_id: string;
  current_stage: string | null;
  completed_stages: string[];
  done: boolean;
  error: string | null;
  twin: { flagged: boolean } | null;
}

interface Props {
  onPatientDone?: () => void;
}

export default function NowProcessingPanel({ onPatientDone }: Props) {
  const [active, setActive] = useState<ActiveStatus | null>(null);
  const lastSeenRequestId = useRef<string | null>(null);
  const notifiedDoneFor = useRef<Set<string>>(new Set());
  const lingerTimeout = useRef<number | null>(null);

  useEffect(() => {
    const poll = async () => {
      const res = await getActivePredictionStream();
      const current = res.active as ActiveStatus | null;

      if (current) {
        lastSeenRequestId.current = current.request_id;
        if (lingerTimeout.current) window.clearTimeout(lingerTimeout.current);
        setActive(current);

        if (current.done && !notifiedDoneFor.current.has(current.request_id)) {
          notifiedDoneFor.current.add(current.request_id);
          onPatientDone?.();
        }
      } else if (lastSeenRequestId.current && !lingerTimeout.current) {
        // Nothing active right now -- but keep the last known result on
        // screen briefly rather than snapping straight to "nothing here".
        lingerTimeout.current = window.setTimeout(() => {
          setActive(null);
          lastSeenRequestId.current = null;
          lingerTimeout.current = null;
        }, LINGER_AFTER_DONE_MS);
      }
    };

    poll();
    const interval = window.setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      window.clearInterval(interval);
      if (lingerTimeout.current) window.clearTimeout(lingerTimeout.current);
    };
  }, []);

  if (!active) return null;

  return (
    <div className="card mb-6 border-blue-200 bg-blue-50/40">
      <div className="flex items-center justify-between mb-3">
        <p className="font-semibold flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          Now Processing: {active.patient_id}
        </p>
        {active.done && active.twin && (
          <span className={active.twin.flagged ? "badge-amber" : "badge-green"}>
            {active.twin.flagged ? "Flagged" : "Cleared"}
          </span>
        )}
        {active.done && active.error && <span className="badge-red">Error</span>}
      </div>
      <PipelineProgress currentStage={active.current_stage} completedStages={active.completed_stages} />
    </div>
  );
}
