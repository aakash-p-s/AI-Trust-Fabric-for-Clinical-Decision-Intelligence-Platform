import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/layout/ProtectedRoute";
import { AuthProvider } from "./contexts/AuthContext";
import Dashboard from "./pages/Dashboard";
import Governance from "./pages/Governance";
import Login from "./pages/Login";
import RulebookSettings from "./pages/RulebookSettings";
import TrustMonitoring from "./pages/TrustMonitoring";
import TwinDetail from "./pages/TwinDetail";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/twins/:twinId"
          element={
            <ProtectedRoute>
              <TwinDetail />
            </ProtectedRoute>
          }
        />
        <Route
          path="/rulebook"
          element={
            <ProtectedRoute requiredRole="compliance_governance">
              <RulebookSettings />
            </ProtectedRoute>
          }
        />
        <Route
          path="/trust-monitoring"
          element={
            <ProtectedRoute requiredRole="compliance_governance">
              <TrustMonitoring />
            </ProtectedRoute>
          }
        />

        <Route
          path="/governance"
          element={
            <ProtectedRoute requiredRole="compliance_governance">
              <Governance />
            </ProtectedRoute>
          }
        />

        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </AuthProvider>
  );
}
