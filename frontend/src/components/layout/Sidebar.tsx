import { LayoutDashboard, ShieldCheck, Activity, ShieldHalf } from "lucide-react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

export default function Sidebar() {
  const { user } = useAuth();
  const isGovernance = user?.role === "compliance_governance";

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium ${
      isActive ? "bg-blue-500/20 border-l-2 border-blue-400 text-white" : "text-gray-300 hover:bg-white/5"
    }`;

  return (
    <aside className="w-[220px] bg-navy text-white flex flex-col justify-between shrink-0">
      <div>
        <div className="flex items-center gap-2 px-4 py-5">
          <ShieldHalf size={22} className="text-blue-400" />
          <span className="font-semibold">AI Trust Fabric</span>
        </div>
        <nav className="flex flex-col gap-1 px-2 mt-2">
          <NavLink to="/dashboard" className={linkClass}>
            <LayoutDashboard size={16} /> Dashboard
          </NavLink>
          {isGovernance && (
            <>
              <NavLink to="/rulebook" className={linkClass}>
                <ShieldCheck size={16} /> Rulebook Settings
              </NavLink>
              <NavLink to="/trust-monitoring" className={linkClass}>
                <Activity size={16} /> Trust Monitoring
              </NavLink>
            </>
          )}
        </nav>
      </div>
    </aside>
  );
}
