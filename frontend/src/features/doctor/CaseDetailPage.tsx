import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { RecommendationCard } from "./RecommendationCard";
import { ConflictBadge } from "@/components/ConflictBadge";

export function CaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const caseId = id!;
  const qc = useQueryClient();

  const caseQ = useQuery({
    queryKey: ["case", caseId],
    queryFn: () => api.getCase(caseId),
  });
  const patientQ = useQuery({
    queryKey: ["patient", caseQ.data?.patient_id],
    queryFn: () => api.getPatient(caseQ.data!.patient_id),
    enabled: !!caseQ.data,
  });
  const recsQ = useQuery({
    queryKey: ["case-recommendations", caseId],
    queryFn: () => api.listCaseRecommendations(caseId),
  });

  // The "open" recommendation is the latest one in a non-terminal state.
  const openRecId = recsQ.data?.find(
    (r) =>
      !["accepted", "overridden", "resolved"].includes(r.state)
  )?.id;
  const openRecQ = useQuery({
    queryKey: ["recommendation", openRecId],
    queryFn: () => api.getRecommendation(openRecId!),
    enabled: !!openRecId,
    refetchInterval: (q) => {
      const state = q.state.data?.state;
      return state === "retrieved" ? 1500 : false;
    },
  });

  const createMut = useMutation({
    mutationFn: () => api.createRecommendation(caseId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["case-recommendations", caseId] });
    },
  });

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-1 space-y-4">
        <div className="card">
          <div className="text-xs uppercase tracking-wide text-slate-500">
            Case
          </div>
          {caseQ.data && (
            <>
              <h1 className="mt-1 text-lg font-semibold">{caseQ.data.title}</h1>
              <p className="text-sm text-slate-600">
                Decision class: {caseQ.data.decision_class.replaceAll("_", " ")}
              </p>
              <p className="text-xs text-slate-500">
                Status: {caseQ.data.status}
              </p>
            </>
          )}
        </div>

        {patientQ.data && (
          <div className="card">
            <div className="text-xs uppercase tracking-wide text-slate-500">
              Patient
            </div>
            <div className="mt-1 font-medium">{patientQ.data.display_name}</div>
            {patientQ.data.demographics.sex && (
              <div className="text-sm text-slate-600">
                Sex: {patientQ.data.demographics.sex}
              </div>
            )}
            <div className="mt-3">
              <div className="text-xs uppercase tracking-wide text-slate-500">
                Conditions
              </div>
              <ul className="mt-1 text-sm">
                {patientQ.data.conditions.map((c) => (
                  <li key={c.id}>{c.label}</li>
                ))}
              </ul>
            </div>
            <div className="mt-3">
              <div className="text-xs uppercase tracking-wide text-slate-500">
                Medications
              </div>
              <ul className="mt-1 text-sm">
                {patientQ.data.medications.map((m) => (
                  <li key={m.id}>
                    {m.label} {m.dose ? `(${m.dose})` : ""}
                  </li>
                ))}
              </ul>
            </div>
            {patientQ.data.allergies.length > 0 && (
              <div className="mt-3">
                <div className="text-xs uppercase tracking-wide text-slate-500">
                  Allergies
                </div>
                <ul className="mt-1 text-sm">
                  {patientQ.data.allergies.map((a) => (
                    <li key={a.id} className="text-red-700">
                      {a.substance} ({a.severity})
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div className="mt-3">
              <div className="text-xs uppercase tracking-wide text-slate-500">
                Latest vitals
              </div>
              {patientQ.data.vitals[0] ? (
                <div className="mt-1 text-sm">
                  BP {patientQ.data.vitals[0].systolic_bp}/
                  {patientQ.data.vitals[0].diastolic_bp}, HR{" "}
                  {patientQ.data.vitals[0].hr}
                </div>
              ) : (
                <div className="text-sm text-slate-500">No vitals recorded.</div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="lg:col-span-2 space-y-4">
        {!openRecId && (
          <div className="card">
            <p className="text-slate-700">No open recommendation.</p>
            <button
              className="btn btn-primary mt-3"
              disabled={createMut.isPending}
              onClick={() => createMut.mutate()}
            >
              {createMut.isPending
                ? "Requesting recommendation…"
                : "Request recommendation"}
            </button>
            {createMut.error && (
              <p className="mt-2 text-sm text-red-700">
                {(createMut.error as Error).message}
              </p>
            )}
          </div>
        )}

        {openRecQ.data && (
          <RecommendationCard
            recommendation={openRecQ.data}
            polling={openRecQ.isFetching}
          />
        )}

        <div className="card">
          <div className="text-xs uppercase tracking-wide text-slate-500">
            Case history
          </div>
          <ul className="mt-2 space-y-2 text-sm">
            {recsQ.data?.map((r) => (
              <li key={r.id} className="flex items-center justify-between">
                <div>
                  <span className="text-slate-600">
                    {new Date(r.created_at).toLocaleString()}
                  </span>{" "}
                  — state {r.state}
                </div>
                <HistoryBadge state={r.state} />
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

function HistoryBadge({ state }: { state: string }) {
  const map: Record<string, "answer" | "retrieve" | "elicit" | "escalate"> = {
    answered: "answer",
    accepted: "answer",
    overridden: "answer",
    resolved: "answer",
    retrieved: "retrieve",
    elicit_pending: "elicit",
    escalated: "escalate",
    under_review: "escalate",
  };
  const routing = map[state];
  const label =
    routing === "answer"
      ? "evidence_gap_resolved"
      : routing === "retrieve"
      ? "evidence_gap_checking"
      : routing === "elicit"
      ? "judgment_call"
      : "under_review";
  return <ConflictBadge label={label} />;
}
