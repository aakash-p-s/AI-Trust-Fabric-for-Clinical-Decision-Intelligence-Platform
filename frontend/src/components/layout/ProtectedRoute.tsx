import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import ChatWidget from "../chat/ChatWidget";
import { useAuth } from "../../contexts/AuthContext";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

interface Props {
  children: ReactNode;
  requiredRole?: "compliance_governance";
}

export default function ProtectedRoute({ children, requiredRole }: Props) {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-auto">
        <Topbar />
        <main className="flex-1 p-6">{children}</main>
      </div>
      <ChatWidget />
    </div>
  );
}
