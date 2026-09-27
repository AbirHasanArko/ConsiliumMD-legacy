import { Navigate } from "react-router-dom";
import { useAuth } from "@/lib/auth";

export function RequireRole({
  roles,
  children,
}: {
  roles: string[];
  children: React.ReactNode;
}) {
  const { user, loading } = useAuth();
  if (loading) return <div className="text-slate-500">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (!roles.some((r) => user.roles.includes(r))) {
    return (
      <div className="card">
        <p className="text-slate-700">
          You don't have access to this view. Required role: {roles.join(" or ")}.
        </p>
      </div>
    );
  }
  return <>{children}</>;
}
