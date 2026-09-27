import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Modal, useModal } from "@/components/Modal";
import { ConflictBadge } from "@/components/ConflictBadge";
import { affordancesForState } from "@/lib/reasoning-states";
import type { RecommendationResponse } from "@/types/api";

interface Props {
  recommendation: RecommendationResponse;
  polling?: boolean;
  onPollingChange?: (polling: boolean) => void;
}

export function RecommendationCard({
  recommendation,
  polling,
  onPollingChange,
}: Props) {
  const qc = useQueryClient();
  const snap = recommendation.snapshot;
  const affordances = affordancesForState(recommendation.state);

  const overrideModal = useModal();
  const escalateModal = useModal();
  const elicitModal = useModal();
  const [rationale, setRationale] = useState("");
  const [note, setNote] = useState("");
  const [selectedOption, setSelectedOption] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const invalidate = () =>
    qc.invalidateQueries({ queryKey: ["recommendation", recommendation.id] });

  const acceptMut = useMutation({
    mutationFn: () => api.acceptRecommendation(recommendation.id),
    onSuccess: invalidate,
  });
  const overrideMut = useMutation({
    mutationFn: () => api.overrideRecommendation(recommendation.id, rationale),
    onSuccess: () => {
      setRationale("");
      overrideModal.hide();
      invalidate();
    },
  });
  const requestEvidenceMut = useMutation({
    mutationFn: () => api.requestEvidence(recommendation.id),
    onSuccess: invalidate,
  });
  const escalateMut = useMutation({
    mutationFn: () => api.escalateRecommendation(recommendation.id, note),
    onSuccess: () => {
      setNote("");
      escalateModal.hide();
      invalidate();
    },
  });
  const elicitMut = useMutation({
    mutationFn: () =>
      api.elicitResponse(recommendation.id, selectedOption),
    onSuccess: () => {
      setSelectedOption("");
      elicitModal.hide();
      invalidate();
    },
  });

  return (
    <div className="card">
      {snap && (
        <div className="flex items-center justify-between gap-3">
          <ConflictBadge label={snap.conflict_label} />
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span>model: {snap.model_version}</span>
            <span>·</span>
            <span>evidence grade: {snap.primary_evidence_grade}</span>
            <span>·</span>
            <span>confidence: {(snap.confidence * 100).toFixed(0)}%</span>
          </div>
        </div>
      )}

      {/* State-specific panel */}
      {affordances.showLoadingPanel && snap && (
        <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
          <div className="flex items-center gap-2">
            <span className="animate-pulse">●</span>
            Checking one more source before answering.
          </div>
          <p className="mt-1 text-xs text-amber-800">
            Reasoning engine has flagged this case for an additional retrieval
            cycle; the page will refresh automatically.
          </p>
        </div>
      )}

      {affordances.showTradeoffPanel && snap && (
        <div className="mt-4 rounded-md border border-blue-200 bg-blue-50 p-3">
          <div className="text-sm font-medium text-blue-900">
            Judgment call — explicit tradeoff
          </div>
          {snap.tradeoff_statement && (
            <p className="mt-2 whitespace-pre-wrap text-sm text-slate-800">
              {snap.tradeoff_statement}
            </p>
          )}
          {snap.elicit_question && (
            <p className="mt-2 text-sm text-slate-700">{snap.elicit_question}</p>
          )}
          <div className="mt-3 grid gap-2 md:grid-cols-3">
            {snap.elicit_options.map((opt) => (
              <button
                key={opt.id}
                type="button"
                className={`btn ${
                  selectedOption === opt.id ? "btn-primary" : "btn-ghost"
                } justify-start text-left`}
                onClick={() => setSelectedOption(opt.id)}
              >
                <div>
                  <div className="font-medium">{opt.label}</div>
                  {opt.description && (
                    <div className="text-xs text-slate-500">{opt.description}</div>
                  )}
                </div>
              </button>
            ))}
          </div>
          <button
            className="btn btn-primary mt-3"
            disabled={!selectedOption || elicitMut.isPending}
            onClick={() => elicitMut.mutate()}
          >
            {elicitMut.isPending ? "Submitting…" : "Submit preference"}
          </button>
        </div>
      )}

      {recommendation.state === "escalated" && snap?.escalation_reason && (
        <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-900">
          <div className="font-medium">Under Review</div>
          <p className="mt-1">{snap.escalation_reason}</p>
          {snap.identifiability_flag === false && (
            <p className="mt-1 text-xs text-red-800">
              Identifiability flag: false — RPD could not classify this
              conflict as purely epistemic or normative.
            </p>
          )}
        </div>
      )}

      {/* Recommendation body */}
      {snap && (
        <div className="mt-4">
          <div className="text-xs uppercase tracking-wide text-slate-500">
            Recommendation
          </div>
          <p className="mt-1 whitespace-pre-wrap text-sm text-slate-900">
            {snap.recommendation_text}
          </p>
        </div>
      )}

      {/* Final state */}
      {(recommendation.state === "accepted" ||
        recommendation.state === "overridden" ||
        recommendation.state === "resolved") && (
        <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-3 text-sm">
          <div className="font-medium">
            Finalized as {recommendation.state}
          </div>
          {recommendation.final_recommendation_text && (
            <p className="mt-1 whitespace-pre-wrap">
              {recommendation.final_recommendation_text}
            </p>
          )}
          {recommendation.final_rationale && (
            <p className="mt-2 text-xs text-slate-600">
              Rationale: {recommendation.final_rationale}
            </p>
          )}
        </div>
      )}

      {/* Reasoning trail */}
      {snap && (
        <details className="mt-4">
          <summary className="cursor-pointer text-sm font-medium text-slate-700">
            Reasoning trail
          </summary>
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-slate-700">
            {snap.reasoning_trail.map((step, i) => (
              <li key={i}>
                <span className="font-medium">{step.step}</span>
                {step.detail ? (
                  <span className="text-slate-500"> — {step.detail}</span>
                ) : null}
              </li>
            ))}
          </ol>
          {recommendation.citations.length > 0 && (
            <div className="mt-3">
              <div className="text-xs uppercase tracking-wide text-slate-500">
                Evidence citations
              </div>
              <ul className="mt-1 space-y-1 text-xs text-slate-700">
                {recommendation.citations.map((c) => (
                  <li key={c.id} className="rounded border border-slate-200 p-2">
                    <div className="font-medium">
                      {c.source_body} — {c.document_title}
                    </div>
                    <div className="text-slate-500">{c.section}</div>
                    <div className="mt-1 italic">{c.excerpt}</div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </details>
      )}

      {error && <p className="mt-2 text-sm text-red-700">{error}</p>}

      {/* Action footer */}
      <div className="mt-4 flex flex-wrap gap-2 border-t border-slate-200 pt-3">
        <button
          className="btn btn-primary"
          disabled={!affordances.canAccept || acceptMut.isPending}
          onClick={() => {
            setError(null);
            acceptMut.mutate(undefined, {
              onError: (e) => setError((e as Error).message),
            });
          }}
        >
          Accept
        </button>
        <button
          className="btn btn-ghost"
          disabled={!affordances.canRequestEvidence || requestEvidenceMut.isPending}
          onClick={() => {
            setError(null);
            requestEvidenceMut.mutate(undefined, {
              onError: (e) => setError((e as Error).message),
            });
          }}
        >
          Request more evidence
        </button>
        <button
          className="btn btn-ghost"
          disabled={!affordances.canEscalate}
          onClick={() => escalateModal.show()}
        >
          Escalate
        </button>
        <button
          className="btn btn-danger"
          disabled={!affordances.canOverride}
          onClick={() => overrideModal.show()}
        >
          Override…
        </button>
        {polling !== undefined && (
          <span className="ml-auto text-xs text-slate-500">
            {polling ? "polling for retrieval…" : ""}
          </span>
        )}
      </div>

      <Modal
        open={overrideModal.open}
        onClose={overrideModal.hide}
        title="Override with rationale"
      >
        <p className="text-sm text-slate-600">
          Overrides are recorded in the audit log and feed the benchmark
          feedback pipeline.
        </p>
        <textarea
          className="input mt-2"
          rows={4}
          value={rationale}
          onChange={(e) => setRationale(e.target.value)}
          placeholder="Why are you overriding the recommendation?"
        />
        <div className="mt-3 flex justify-end gap-2">
          <button className="btn btn-ghost" onClick={overrideModal.hide}>
            Cancel
          </button>
          <button
            className="btn btn-danger"
            disabled={!rationale.trim() || overrideMut.isPending}
            onClick={() => {
              setError(null);
              overrideMut.mutate(undefined, {
                onError: (e) => setError((e as Error).message),
              });
            }}
          >
            Submit override
          </button>
        </div>
      </Modal>

      <Modal
        open={escalateModal.open}
        onClose={escalateModal.hide}
        title="Escalate to senior clinician"
      >
        <p className="text-sm text-slate-600">
          The case will appear in the senior clinician queue.
        </p>
        <textarea
          className="input mt-2"
          rows={3}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Optional note for the reviewer"
        />
        <div className="mt-3 flex justify-end gap-2">
          <button className="btn btn-ghost" onClick={escalateModal.hide}>
            Cancel
          </button>
          <button
            className="btn btn-primary"
            disabled={escalateMut.isPending}
            onClick={() => {
              setError(null);
              escalateMut.mutate(undefined, {
                onError: (e) => setError((e as Error).message),
              });
            }}
          >
            Escalate
          </button>
        </div>
      </Modal>
    </div>
  );
}
