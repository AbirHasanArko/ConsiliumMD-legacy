import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "@/lib/auth";

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const roles = user?.roles ?? [];
  const isAdmin = roles.includes("admin");
  const isDoctor = roles.includes("doctor");
  const isReviewer = roles.includes("senior_clinician");

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/" className="text-lg font-semibold tracking-tight">
              ConsiliumMD
            </Link>
            <span className="text-xs text-slate-500">
              decision-support (not a diagnostic device)
            </span>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-slate-600">{user?.full_name}</span>
            <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-700">
              {roles.join(", ") || "no role"}
            </span>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                logout();
                navigate("/login");
              }}
            >
              Sign out
            </button>
          </div>
        </div>
        <nav className="mx-auto max-w-6xl px-6 pb-3 flex gap-4 text-sm">
          {isDoctor && (
            <NavLink to="/doctor" className={navClass}>
              Doctor dashboard
            </NavLink>
          )}
          {isReviewer && (
            <NavLink to="/reviewer" className={navClass}>
              Reviewer queue
            </NavLink>
          )}
          {isAdmin && (
            <>
              <NavLink to="/admin/users" className={navClass}>
                Users
              </NavLink>
              <NavLink to="/admin/audit" className={navClass}>
                Audit log
              </NavLink>
              <NavLink to="/admin/models" className={navClass}>
                Model versions
              </NavLink>
            </>
          )}
        </nav>
      </header>
      <main className="flex-1">
        <div className="mx-auto max-w-6xl px-6 py-6">
          <Outlet />
        </div>
      </main>
      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-3 text-xs text-slate-500">
          ConsiliumMD is a decision-support tool, not a diagnostic device.
          Every recommendation requires explicit clinician action and is
          recorded in the audit log.
        </div>
      </footer>
    </div>
  );
}

function navClass({ isActive }: { isActive: boolean }) {
  return [
    "rounded-md px-2 py-1",
    isActive ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100",
  ].join(" ");
}
