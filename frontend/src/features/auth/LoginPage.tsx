import { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "@/lib/auth";

export function LoginPage() {
  const { user, login } = useAuth();
  const [email, setEmail] = useState("doctor@consilium.md");
  const [password, setPassword] = useState("doctor1234");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  if (user) {
    const landing =
      user.roles.includes("admin") && !user.roles.includes("doctor")
        ? "/admin/users"
        : user.roles.includes("senior_clinician") && !user.roles.includes("doctor")
        ? "/reviewer"
        : "/doctor";
    return <Navigate to={landing} replace />;
  }

  return (
    <div className="mx-auto mt-20 max-w-md">
      <div className="card">
        <h1 className="text-lg font-semibold">Sign in to ConsiliumMD</h1>
        <p className="mt-1 text-sm text-slate-600">
          Decision-support for clinicians. Demo credentials are pre-filled —
          this is a development environment.
        </p>
        <form
          className="mt-4 space-y-3"
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError(null);
            try {
              await login(email, password);
              navigate("/doctor");
            } catch (err) {
              setError((err as Error).message || "Login failed");
            } finally {
              setBusy(false);
            }
          }}
        >
          <div>
            <label className="block text-sm font-medium text-slate-700">
              Email
            </label>
            <input
              type="email"
              required
              className="input mt-1"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">
              Password
            </label>
            <input
              type="password"
              required
              className="input mt-1"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && <p className="text-sm text-red-700">{error}</p>}
          <button className="btn btn-primary w-full" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-slate-500">
          <div>
            <div className="font-medium text-slate-700">Demo users</div>
            <div>doctor@consilium.md / doctor1234</div>
            <div>reviewer@consilium.md / reviewer1234</div>
            <div>admin@consilium.md / admin1234</div>
          </div>
        </div>
      </div>
    </div>
  );
}
