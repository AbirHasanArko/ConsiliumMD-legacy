import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function ModelVersionsPage() {
  const versionsQ = useQuery({
    queryKey: ["model-versions"],
    queryFn: api.listModelVersions,
  });
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Model versions</h1>
      <p className="text-sm text-slate-600">
        Every recommendation references a model_version_id. The audit log
        preserves the link so historical recommendations are reconstructable.
      </p>
      <div className="card overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500">
              <th className="py-2 pr-4">Provider</th>
              <th className="py-2 pr-4">Name</th>
              <th className="py-2 pr-4">Active</th>
              <th className="py-2 pr-4">Recommendations</th>
            </tr>
          </thead>
          <tbody>
            {versionsQ.data?.map((v) => (
              <tr key={v.model_version_id} className="border-t border-slate-100">
                <td className="py-2 pr-4">{v.provider}</td>
                <td className="py-2 pr-4 font-mono text-xs">{v.name}</td>
                <td className="py-2 pr-4">{v.is_active ? "yes" : "no"}</td>
                <td className="py-2 pr-4">{v.recommendation_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
