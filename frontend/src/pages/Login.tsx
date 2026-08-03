import { Activity, Eye, EyeOff, Link2, MessageSquare, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { login as loginApi } from "../lib/api";

const FEATURES = [
  {
    icon: Link2,
    title: "Full Lineage",
    desc: "Trace every prediction back to its source data and model version",
  },
  {
    icon: ShieldCheck,
    title: "Compliance Built-In",
    desc: "Automatic checks against approved versions and thresholds",
  },
  {
    icon: MessageSquare,
    title: "Plain-English Explanations",
    desc: "AI reasoning translated into clinical language",
  },
  {
    icon: Activity,
    title: "Continuous Trust Monitoring",
    desc: "Drift and confidence tracked over time, not just at prediction time",
  },
];

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const result = await loginApi(username, password);
      if (result.success && result.user) {
        login(result.user);
        navigate("/dashboard");
      } else {
        setError(result.error || "Invalid credentials");
        setPassword("");
      }
    } catch {
      setError("Could not reach the server. Is the backend running?");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen grid grid-cols-1 md:grid-cols-2">
      {/* Left hero panel */}
      <div className="bg-navy text-white p-12 flex flex-col justify-center">
        <h1 className="text-4xl font-bold mb-2">Trust Fabric</h1>
        <p className="text-blue-300 text-sm tracking-widest mb-4">DIGITAL COMPLIANCE TWIN // v1</p>
        <p className="text-gray-300 mb-10 max-w-md">
          Every AI clinical prediction, automatically explained, checked, and made defensible.
        </p>
        <div className="flex flex-col gap-6">
          {FEATURES.map((f) => (
            <div key={f.title} className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg border border-white/20 flex items-center justify-center shrink-0">
                <f.icon size={18} className="text-blue-300" />
              </div>
              <div>
                <p className="font-medium">{f.title}</p>
                <p className="text-sm text-gray-400">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right sign-in panel */}
      <div className="flex items-center justify-center p-8 bg-gray-50">
        <div className="w-full max-w-sm">
          <p className="text-xs text-gray-400 mb-1">Authenticate to continue</p>
          <h2 className="text-2xl font-semibold mb-6">Sign In</h2>

          {error && (
            <div className="border border-red-300 bg-red-50 text-red-700 text-sm rounded-lg px-3 py-2 mb-4">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Username / ID</label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username or ID"
                required
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm pr-9"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  className="absolute right-3 top-2.5 text-gray-400"
                  onClick={() => setShowPassword((s) => !s)}
                  aria-label="Toggle password visibility"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            <button type="submit" className="btn-primary w-full py-2.5" disabled={submitting}>
              {submitting ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <p className="text-xs text-gray-400 text-center mt-6">
            Role is resolved automatically from your credentials.
          </p>
        </div>
      </div>
    </div>
  );
}
