import { Check, Loader2 } from "lucide-react";

const STAGES: { key: string; label: string }[] = [
  { key: "lineage", label: "Lineage" },
  { key: "compliance", label: "Compliance" },
  { key: "explainability", label: "Explainability" },
  { key: "twin_assembler", label: "Twin Assembler" },
];

interface Props {
  currentStage: string | null;
  completedStages: string[];
}

export default function PipelineProgress({ currentStage, completedStages }: Props) {
  return (
    <div className="flex items-center gap-2">
      {STAGES.map((stage, i) => {
        const isDone = completedStages.includes(stage.key);
        const isActive = currentStage === stage.key && !isDone;

        return (
          <div key={stage.key} className="flex items-center gap-2">
            <div
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border ${
                isDone
                  ? "border-green-300 bg-green-50 text-green-700"
                  : isActive
                  ? "border-blue-300 bg-blue-50 text-blue-700"
                  : "border-gray-200 bg-gray-50 text-gray-400"
              }`}
            >
              {isDone && <Check size={13} />}
              {isActive && <Loader2 size={13} className="animate-spin" />}
              {stage.label}
            </div>
            {i < STAGES.length - 1 && (
              <div className={`w-4 h-px ${isDone ? "bg-green-300" : "bg-gray-200"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
