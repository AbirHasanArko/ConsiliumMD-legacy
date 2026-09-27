# Architecture notes

This document is the longer-form companion to the README's architecture section.

## Layered design

```
┌────────────────────┐
│   React frontend   │  role-gated routes, single shell
└─────────┬──────────┘
          │ REST (+ optional WS for live updates)
┌─────────▼──────────┐
│   FastAPI gateway  │  auth, RBAC, rate limiting
└─────────┬──────────┘
          │
   ┌──────┼─────────────────────┐
   │      │                     │
┌──▼───┐ ┌▼─────────────┐  ┌────▼───────────┐
│ EHR/ │ │ Reasoning    │  │ Audit &        │
│ pt   │ │ Service      │  │ Compliance     │
│ data │ │ (Provider    │  │ Service        │
│      │ │  protocol)   │  │                │
└──────┘ └──────┬───────┘  └────────────────┘
               │ HTTP (Phase 2)
        ┌──────▼───────┐
        │    CARMA     │
        └──────────────┘
```

## Where logic lives

- **Auth & RBAC** — `backend/app/core/`, `backend/app/deps.py`. The
  permission matrix is explicit (`rbac.PERMISSIONS`) so a security review can
  read it as a single file.
- **Reasoning** — `backend/app/services/reasoning/`. The rest of the codebase
  speaks only in `RoutingDecision` + `ConflictTypeLabel`. Mock and CARMA are
  both implementations of the same protocol.
- **Audit** — `backend/app/services/audit.py`. Every endpoint that mutates
  state goes through this writer. The writer is *transactional* — it lives
  in the same DB transaction as the business write, so partial state is
  unreachable.
- **Safety auditor** — `backend/app/services/safety_auditor.py`. Pure rule
  check against the patient's own record (allergies, contraindications).
  Runs server-side before the recommendation is shown.

## Frontend structure

- `features/auth` — login, JWT storage, route guards.
- `features/doctor` — dashboard, case detail, recommendation card.
- `features/reviewer` — queue, resolve.
- `features/admin` — users, audit log, model versions.
- `components/` — design-system primitives (`Card`, `Badge`, `Modal`,
  `Button`, `EmptyState`, `Spinner`).
- `lib/reasoning-states.ts` — single source of truth for the mapping
  between `RoutingDecision` ↔ `ConflictTypeLabel` ↔ UI affordances.

## Data flow for a fresh recommendation

```
1. Doctor opens case detail page (GET /cases/{id}).
2. Page sees no pending recommendation → calls POST /cases/{id}/recommendations.
3. Backend:
   a. Loads case, patient context, decision class.
   b. Calls scope service → 409 if out of scope.
   c. Calls orchestrator.reason(req) → MockProvider returns ReasoningResponse.
   d. Writes recommendation row (state=pending or terminal of the response).
   e. Writes reasoning_snapshot row (immutable).
   f. Writes evidence_citations rows.
   g. Writes audit_events row (recommendation.create).
   h. Runs safety_auditor.check() — appends a snapshot note + audit event if
      anything fires.
4. Frontend renders recommendation card.
5. Doctor clicks Accept → POST /recommendations/{id}/accept.
6. Backend:
   a. Loads recommendation, validates state ∈ {answered, elicit_pending}.
   b. Updates state=accepted, writes action_log + audit_events in same tx.
   c. Returns updated recommendation.
7. Frontend re-renders the card in its terminal state.
```

The recommendation card has no `accept` button visible until `state=answered`,
which is enforced both server-side (state check) and client-side (button
hidden). Belt and suspenders.

## Why the four routing states are non-negotiable

A clinician looking at the product should always be able to answer: "what is
this case doing right now?" The answer is always one of four options. There
is no fifth "system is thinking, who knows" state. This is enforced by:

- The `routing_decision` enum on `reasoning_snapshots` — exactly four values.
- The `conflict_label` enum — derived deterministically from `routing_decision`.
- The recommendation card UI — has a component for each state, no fallback.
- The state machine — invalid transitions return 409.

When CARMA's `RoutingDecision` adds a new value in the future, that change is
a single edit in `backend/app/services/reasoning/states.py` (and the
mirroring `lib/reasoning-states.ts`), with all four callers updated.
