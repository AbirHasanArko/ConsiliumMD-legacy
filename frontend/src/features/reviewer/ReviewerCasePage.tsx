import { useParams, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { RecommendationCard } from "@/features/doctor/RecommendationCard";

export function ReviewerCasePage() {
  const { id } = useParams<{ id: string }>();
  const recId = id!;
  const navigate = useNavigate();
  const qc = useQueryClient();

  const recQ = useQuery({
    queryKey: ["recommendation", recId],
    queryFn: () => api.getRecommendation(recId),
  });
  const [finalText, setFinalText] = useState("");
  const [rationale, setRationale] = useState("");
  const resolveMut = useMutation({
    mutationFn: () => api.resolveRecommendation(recId, finalText, rationale),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["review-queue"] });
      navigate("/reviewer");
    },
  });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Senior review</h1>
        <p className="text-sm text-slate-600">
          Resolve the case with a final recommendation and rationale.
        </p>
      </div>
      {recQ.data && <RecommendationCard recommendation={recQ.data} />}

      {recQ.data &&
        (recQ.data.state === "escalated" ||
          recQ.data.state === "under_review") && (
          <div className="card">
            <div className="text-sm font-medium">Resolve</div>
            <label className="mt-2 block text-xs text-slate-600">
              Final recommendation
            </label>
            <textarea
              className="input"
              rows={3}
              value={finalText}
              onChange={(e) => setFinalText(e.target.value)}
            />
            <label className="mt-2 block text-xs text-slate-600">
              Rationale
            </label>
            <textarea
              className="input"
              rows={3}
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
            />
            <button
              className="btn btn-primary mt-3"
              disabled={
                !finalText.trim() || !rationale.trim() || resolveMut.isPending
              }
              onClick={() => resolveMut.mutate()}
            >
              {resolveMut.isPending ? "Resolving…" : "Resolve"}
            </button>
            {resolveMut.error && (
              <p className="mt-2 text-sm text-red-700">
                {(resolveMut.error as Error).message}
              </p>
            )}
          </div>
        )}
    </div>
  );
}
