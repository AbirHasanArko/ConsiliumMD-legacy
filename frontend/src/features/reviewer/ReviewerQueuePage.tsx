import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ConflictBadge } from "@/components/ConflictBadge";

export function ReviewerQueuePage() {
  const queueQ = useQuery({
    queryKey: ["review-queue"],
    queryFn: api.reviewQueue,
  });
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Reviewer queue</h1>
        <p className="text-sm text-slate-600">
          Cases routed here are either under review or awaiting reviewer action.
        </p>
      </div>
      {queueQ.isLoading && <p className="text-slate-500">Loading queue…</p>}
      {queueQ.data && queueQ.data.length === 0 && (
        <div className="card text-slate-600">
          Nothing in the queue. (Escalated cases appear here.)
        </div>
      )}
      <ul className="space-y-3">
        {queueQ.data?.map((r) => (
          <li key={r.id} className="card">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">{r.case_id.slice(0, 8)}…</div>
                <div className="text-sm text-slate-500">
                  Created {new Date(r.created_at).toLocaleString()}
                </div>
              </div>
              <ConflictBadge
                label={r.state === "under_review" ? "under_review" : "judgment_call"}
              />
            </div>
            <Link
              to={`/reviewer/cases/${r.id}`}
              className="btn btn-ghost mt-3"
            >
              Open
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
