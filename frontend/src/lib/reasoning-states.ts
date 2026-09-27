// Single source of truth (frontend side) for the mapping between
// `RoutingDecision` ↔ `ConflictTypeLabel` ↔ UI affordances.
//
// Mirrors backend/app/services/reasoning/states.py.

import type { ConflictTypeLabel, RoutingDecision } from "@/types/api";

export const CONFLICT_LABEL_FOR_ROUTING: Record<
  RoutingDecision,
  ConflictTypeLabel
> = {
  answer: "evidence_gap_resolved",
  retrieve: "evidence_gap_checking",
  elicit: "judgment_call",
  escalate: "under_review",
};

export const CONFLICT_LABEL_TEXT: Record<ConflictTypeLabel, string> = {
  evidence_gap_resolved: "Evidence Gap — resolved",
  evidence_gap_checking: "Evidence Gap — checking further",
  judgment_call: "Judgment Call",
  under_review: "Under Review",
};

export const CONFLICT_LABEL_BADGE_CLASS: Record<ConflictTypeLabel, string> = {
  evidence_gap_resolved: "badge badge-resolved",
  evidence_gap_checking: "badge badge-checking",
  judgment_call: "badge badge-judgment",
  under_review: "badge badge-review",
};

export interface RecommendationUiAffordances {
  canAccept: boolean;
  canRequestEvidence: boolean;
  canEscalate: boolean;
  canOverride: boolean;
  canResolve: boolean;
  canSubmitElicit: boolean;
  showTradeoffPanel: boolean;
  showLoadingPanel: boolean;
}

export function affordancesForState(state: string): RecommendationUiAffordances {
  switch (state) {
    case "answered":
      return {
        canAccept: true,
        canRequestEvidence: true,
        canEscalate: true,
        canOverride: true,
        canResolve: false,
        canSubmitElicit: false,
        showTradeoffPanel: false,
        showLoadingPanel: false,
      };
    case "retrieved":
      return {
        canAccept: false,
        canRequestEvidence: true,
        canEscalate: true,
        canOverride: false,
        canResolve: false,
        canSubmitElicit: false,
        showTradeoffPanel: false,
        showLoadingPanel: true,
      };
    case "elicit_pending":
      return {
        canAccept: false,
        canRequestEvidence: false,
        canEscalate: true,
        canOverride: false,
        canResolve: false,
        canSubmitElicit: true,
        showTradeoffPanel: true,
        showLoadingPanel: false,
      };
    case "escalated":
      return {
        canAccept: false,
        canRequestEvidence: false,
        canEscalate: false,
        canOverride: false,
        canResolve: true,
        showTradeoffPanel: false,
        showLoadingPanel: false,
        canSubmitElicit: false,
      };
    case "under_review":
      return {
        canAccept: false,
        canRequestEvidence: false,
        canEscalate: false,
        canOverride: false,
        canResolve: true,
        showTradeoffPanel: false,
        showLoadingPanel: false,
        canSubmitElicit: false,
      };
    default:
      return {
        canAccept: false,
        canRequestEvidence: false,
        canEscalate: false,
        canOverride: false,
        canResolve: false,
        showTradeoffPanel: false,
        showLoadingPanel: false,
        canSubmitElicit: false,
      };
  }
}

export const TERMINAL_STATES = new Set([
  "accepted",
  "overridden",
  "resolved",
]);
