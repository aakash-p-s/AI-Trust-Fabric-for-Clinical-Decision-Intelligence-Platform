import { useEffect, useRef, useState } from "react";
import { getDemoPatients, getPredictionStreamStatus, startPredictionStream } from "../../lib/api";
import PipelineProgress from "./PipelineProgress";

const POLL_INTERVAL_MS = 400;

interface DemoPatient {
  patient_id: string;
  model_name: string;
  model_version: string;
  prediction: string;
  confidence: number;
  timestamp: string;
}

interface Props {
  onTwinCreated: () => void; // lets the Dashboard refresh its table immediately
}

export default function LiveDemoPanel({ onTwinCreated }: Props) {
  const [patients, setPatients] = useState<DemoPatient[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [currentStage, setCurrentStage] = useState<string | null>(null);
  const [completedStages, setCompletedStages] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [resultLabel, setResultLabel] = useState<string | null>(null);

  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    getDemoPatients()
      .then((res) => setPatients(res.patients as unknown as DemoPatient[]))
      .catch(() => {});
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, []);

  const sendSelected = async () => {
    const record = patients[selectedIndex];
    if (!record) return;

    setRunning(true);
    setResultLabel(null);
    setCurrentStage(null);
    setCompletedStages([]);

    const { request_id } = await startPredictionStream(record);

    pollRef.current = window.setInterval(async () => {
      const status = await getPredictionStreamStatus(request_id);
      setCurrentStage(status.current_stage);
      setCompletedStages(status.completed_stages);

      if (status.done) {
        if (pollRef.current) window.clearInterval(pollRef.current);
        setRunning(false);
        if (status.error) {
          setResultLabel(`Error: ${status.error}`);
        } else if (status.twin) {
          setResultLabel(status.twin.flagged ? "Flagged for review" : "Cleared");
          onTwinCreated();
        }
      }
    }, POLL_INTERVAL_MS);
  };

  return (
    <div className="card mb-6">
      <div className="flex items-center justify-between mb-3">
        <p className="font-semibold">Live Pipeline Demo</p>
        {resultLabel && (
          <span className={resultLabel.includes("Flagged") ? "badge-amber" : resultLabel.includes("Error") ? "badge-red" : "badge-green"}>
            {resultLabel}
          </span>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-4">
        <select
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
          value={selectedIndex}
          onChange={(e) => setSelectedIndex(Number(e.target.value))}
          disabled={running}
        >
          {patients.map((p, i) => (
            <option key={p.patient_id} value={i}>
              {p.patient_id} — {p.prediction} ({p.model_version}, {(p.confidence * 100).toFixed(0)}%)
            </option>
          ))}
        </select>
        <button className="btn-primary" onClick={sendSelected} disabled={running || patients.length === 0}>
          {running ? "Processing..." : "Send Selected Patient"}
        </button>
      </div>

      <PipelineProgress currentStage={currentStage} completedStages={completedStages} />
    </div>
  );
}
