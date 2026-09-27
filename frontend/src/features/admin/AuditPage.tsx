import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function AuditPage() {
  const [actionFilter, setActionFilter] = useState("");
  const eventsQ = useQuery({
    queryKey: ["audit-events", actionFilter],
    queryFn: () =>
      api.listAuditEvents({
        action: actionFilter || undefined,
        limit: 200,
      }),
  });
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Audit log</h1>
        <a
          className="btn btn-ghost"
          href={api.auditCsvUrl()}
          target="_blank"
          rel="noreferrer"
        >
          Export CSV
        </a>
      </div>
      <div className="card">
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-600">Filter by action:</label>
          <input
            className="input max-w-xs"
            placeholder="e.g. recommendation.accept"
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
          />
        </div>
      </div>
      <div className="card overflow-x-auto">
        <table className="min-w-full text-xs">
          <thead>
            <tr className="text-left text-slate-500">
              <th className="py-2 pr-4">When</th>
              <th className="py-2 pr-4">Actor</th>
              <th className="py-2 pr-4">Action</th>
              <th className="py-2 pr-4">Target</th>
              <th className="py-2 pr-4">Payload</th>
            </tr>
          </thead>
          <tbody>
            {eventsQ.data?.map((e) => (
              <tr key={e.id} className="border-t border-slate-100">
                <td className="py-2 pr-4 text-slate-600">
                  {new Date(e.occurred_at).toLocaleString()}
                </td>
                <td className="py-2 pr-4 font-mono">
                  {e.actor_user_id?.slice(0, 8) ?? "—"}
                </td>
                <td className="py-2 pr-4 font-medium">{e.action}</td>
                <td className="py-2 pr-4 text-slate-600">
                  {e.target_type}
                  {e.target_id ? `/${e.target_id.slice(0, 8)}` : ""}
                </td>
                <td className="py-2 pr-4 font-mono text-[10px] text-slate-500">
                  <code>{e.payload_json}</code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
