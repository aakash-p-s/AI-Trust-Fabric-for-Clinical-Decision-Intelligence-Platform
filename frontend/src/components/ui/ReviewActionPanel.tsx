import { useState } from "react";

interface Props {
  onApprove: (notes: string) => Promise<void>;
  onOverride: (notes: string) => Promise<void>;
}

const MAX_NOTES = 1000;

export default function ReviewActionPanel({ onApprove, onOverride }: Props) {
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleApprove = async () => {
    setSubmitting(true);
    try {
      await onApprove(notes);
    } finally {
      setSubmitting(false);
    }
  };

  const handleOverride = async () => {
    setSubmitting(true);
    try {
      await onOverride(notes);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card mt-4">
      <p className="font-semibold mb-1">Compliance Action</p>
      <p className="text-sm text-gray-500 mb-3">
        Review the AI prediction and compliance results. Choose an action below.
      </p>
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex gap-3">
          <button className="btn-primary bg-green-600" disabled={submitting} onClick={handleApprove}>
            Approve
          </button>
          <button
            className="btn-danger"
            disabled={submitting || notes.trim().length === 0}
            onClick={handleOverride}
          >
            Override
          </button>
        </div>
        <div className="flex-1">
          <label className="text-xs text-gray-500 block mb-1">
            Override requires a reason (required)
          </label>
          <textarea
            className="w-full border border-gray-200 rounded-lg p-2 text-sm"
            rows={2}
            maxLength={MAX_NOTES}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Provide a clear reason for overriding this prediction..."
          />
          <p className="text-xs text-gray-400 text-right">
            {notes.length}/{MAX_NOTES}
          </p>
        </div>
      </div>
    </div>
  );
}
