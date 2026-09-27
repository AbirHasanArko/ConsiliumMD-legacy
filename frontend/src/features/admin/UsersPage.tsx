import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function UsersPage() {
  const usersQ = useQuery({ queryKey: ["users"], queryFn: api.listUsers });
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Users</h1>
      <div className="card overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500">
              <th className="py-2 pr-4">Email</th>
              <th className="py-2 pr-4">Name</th>
              <th className="py-2 pr-4">Roles</th>
              <th className="py-2 pr-4">Active</th>
              <th className="py-2 pr-4">Created</th>
            </tr>
          </thead>
          <tbody>
            {usersQ.data?.map((u) => (
              <tr key={u.id} className="border-t border-slate-100">
                <td className="py-2 pr-4 font-mono text-xs">{u.email}</td>
                <td className="py-2 pr-4">{u.full_name}</td>
                <td className="py-2 pr-4 text-xs text-slate-600">
                  {u.roles.join(", ")}
                </td>
                <td className="py-2 pr-4">{u.is_active ? "yes" : "no"}</td>
                <td className="py-2 pr-4 text-xs text-slate-500">
                  {new Date(u.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
