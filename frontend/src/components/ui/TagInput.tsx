import { X } from "lucide-react";
import { useState } from "react";

interface TagInputProps {
  values: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
}

export default function TagInput({ values, onChange, placeholder }: TagInputProps) {
  const [draft, setDraft] = useState("");

  const addTag = () => {
    const trimmed = draft.trim();
    if (trimmed && !values.includes(trimmed)) {
      onChange([...values, trimmed]);
    }
    setDraft("");
  };

  const removeTag = (tag: string) => {
    onChange(values.filter((v) => v !== tag));
  };

  return (
    <div className="border border-gray-200 rounded-lg p-3">
      <div className="flex flex-wrap gap-2 mb-2">
        {values.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center gap-1 bg-blue-50 text-blue-700 text-sm px-2.5 py-1 rounded-md"
          >
            {tag}
            <button onClick={() => removeTag(tag)} aria-label={`Remove ${tag}`}>
              <X size={14} />
            </button>
          </span>
        ))}
      </div>
      <input
        className="w-full text-sm border-none outline-none placeholder:text-gray-400"
        placeholder={placeholder || "Add a value and press Enter"}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            addTag();
          }
        }}
      />
    </div>
  );
}
