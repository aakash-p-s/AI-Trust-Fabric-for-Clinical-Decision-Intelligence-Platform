import { ChevronDown } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { initials } from "../../lib/utils";

const ROLE_LABEL: Record<string, string> = {
  clinician: "Clinician",
  compliance_governance: "Compliance/Governance",
};

export default function Topbar() {
  const { user, logout } = useAuth();

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <div className="flex items-center gap-2 text-sm text-gray-600">
        Global Health System <ChevronDown size={14} />
      </div>
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-semibold">
          {user ? initials(user.display_name) : ""}
        </div>
        <div className="text-sm">
          <p className="font-medium leading-tight">{user?.display_name}</p>
          <p className="text-xs text-gray-400 leading-tight">
            {user ? ROLE_LABEL[user.role] : ""}
          </p>
        </div>
        <button onClick={logout} className="text-xs text-gray-400 hover:text-gray-700 ml-2">
          Logout
        </button>
      </div>
    </header>
  );
}
