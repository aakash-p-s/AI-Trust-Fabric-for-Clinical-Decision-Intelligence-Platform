import { useEffect, useState } from "react";
import ChangeLogTable from "../components/ui/ChangeLogTable";
import TagInput from "../components/ui/TagInput";
import { useAuth } from "../contexts/AuthContext";
import { getRulebook, getRulebookChangelog, updateRulebook } from "../lib/api";
import type { ChangelogEntry, ComplianceRulebook } from "../lib/types";

export default function RulebookSettings() {
  const { user } = useAuth();
  const [rulebook, setRulebook] = useState<ComplianceRulebook | null>(null);
  const [changelog, setChangelog] = useState<ChangelogEntry[]>([]);
  const [toast, setToast] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = () => {
    getRulebook().then(setRulebook);
    getRulebookChangelog().then((r) => setChangelog(r.entries));
  };

  useEffect(load, []);

  if (!rulebook) return <p className="text-gray-400">Loading...</p>;

  const handleSave = async () => {
    if (!user) return;
    setSaving(true);
    try {
      await updateRulebook(rulebook, user.username, user.role);
      setToast("Settings saved successfully.");
      load();
      setTimeout(() => setToast(null), 3000);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <p className="text-xs text-gray-400">Dashboard &gt; Rulebook Settings</p>
        {toast && <span className="badge-green">{toast}</span>}
      </div>
      <div className="flex items-center gap-2 mb-4">
        <h1 className="text-xl font-semibold">Rulebook Settings</h1>
        <span className="badge-gray">Compliance/Governance only</span>
      </div>

      <div className="card mb-4">
        <p className="font-semibold mb-1">Approved Model Versions</p>
        <p className="text-xs text-gray-500 mb-2">Select the model versions that are approved for production use.</p>
        <TagInput
          values={rulebook.approved_model_versions}
          onChange={(v) => setRulebook({ ...rulebook, approved_model_versions: v })}
          placeholder="Add a model version and press Enter"
        />
      </div>

      <div className="card mb-4">
        <p className="font-semibold mb-1">Confidence Threshold</p>
        <p className="text-xs text-gray-500 mb-3">
          Set the minimum confidence score required for predictions to be auto-cleared.
        </p>
        <div className="flex items-center gap-4">
          <input
            type="number"
            step={0.01}
            min={0}
            max={1}
            className="w-24 border border-gray-300 rounded-lg px-2 py-1.5 text-sm"
            value={rulebook.minimum_confidence_threshold}
            onChange={(e) =>
              setRulebook({ ...rulebook, minimum_confidence_threshold: parseFloat(e.target.value) })
            }
          />
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            className="flex-1"
            value={rulebook.minimum_confidence_threshold}
            onChange={(e) =>
              setRulebook({ ...rulebook, minimum_confidence_threshold: parseFloat(e.target.value) })
            }
          />
          <span className="text-xs text-gray-400">Range: 0.0 - 1.0</span>
        </div>
      </div>

      <div className="card mb-4">
        <p className="font-semibold mb-1">High-Risk Conditions</p>
        <p className="text-xs text-gray-500 mb-2">Define conditions that always require human review.</p>
        <TagInput
          values={rulebook.high_risk_conditions_requiring_review}
          onChange={(v) => setRulebook({ ...rulebook, high_risk_conditions_requiring_review: v })}
          placeholder="Add a condition and press Enter"
        />
      </div>

      <div className="flex justify-end mb-4">
        <button className="btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? "Saving..." : "Save Changes"}
        </button>
      </div>

      <div className="card">
        <p className="font-semibold mb-1">Change Log</p>
        <p className="text-xs text-gray-500 mb-3">Recent changes to rulebook settings.</p>
        <ChangeLogTable entries={changelog} />
      </div>
    </div>
  );
}
