import type { ChangelogEntry } from "../../lib/types";
import { initials } from "../../lib/utils";

export default function ChangeLogTable({ entries }: { entries: ChangelogEntry[] }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left text-gray-500 border-b border-gray-200">
          <th className="py-2 font-medium">User</th>
          <th className="py-2 font-medium">Change</th>
          <th className="py-2 font-medium">Date &amp; Time</th>
        </tr>
      </thead>
      <tbody>
        {entries.map((entry, i) => (
          <tr key={i} className="border-b border-gray-100">
            <td className="py-2">
              <span className="inline-flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-gray-200 text-xs flex items-center justify-center">
                  {initials(entry.changed_by)}
                </span>
                {entry.changed_by}
              </span>
            </td>
            <td className="py-2">{entry.change_description}</td>
            <td className="py-2 text-gray-500">{new Date(entry.changed_at).toLocaleString()}</td>
          </tr>
        ))}
        {entries.length === 0 && (
          <tr>
            <td colSpan={3} className="py-4 text-center text-gray-400">
              No changes recorded yet.
            </td>
          </tr>
        )}
      </tbody>
    </table>
  );
}
