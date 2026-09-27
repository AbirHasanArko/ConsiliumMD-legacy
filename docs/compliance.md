# Compliance & Safety

This document captures how ConsiliumMD operationalizes the safety, compliance,
and ethical guardrails from the product spec §6 — not in docs, but in code.

## Principles

1. **No autonomous action.** No endpoint places an order, prescribes, or
   updates a chart. Every state-changing action requires an authenticated,
   authorized human click and writes an audit event.
2. **Uncertainty is always visible.** Recommendation cards render the
   conflict-type badge and confidence in every state. There is no UI affordance
   to hide them.
3. **Every judgment-call case surfaces the tradeoff.** When the engine routes
   to `ELICIT`, the response must populate `tradeoff_statement` and
   `elicit_options`; the recommendation card refuses to render `ELICIT` state
   without these fields.
4. **Full auditability.** `audit_events` is DB-trigger-protected append-only.
   The CSV export streams and is admin-gated.
5. **Explicit informed consent.** The `consents` table exists today even
   though the patient portal is Phase 4. Recording a consent does not unlock
   any feature in MVP — patient-scope is off.
6. **Data protection.** Treat as HIPAA-equivalent regardless of jurisdiction.
   All passwords bcrypt-hashed, JWT signed, role-scoped endpoints, minimal
   retention policy enforced via scheduled jobs in Phase 3.
7. **Escalation is first-class.** The reviewer queue is a full-page route with
   its own RBAC role, not an afterthought.
8. **Decision-support, not a diagnostic device.** Every user-visible surface
   carries that label (login page footer, recommendation card footer, audit
   export header).

## Decision-class scope enforcement

The MVP-eligible decision classes are listed in the spec §8. The two normative
classes that are held back pending ethics review are:

| Decision class | Spec rationale | Scope row |
|---|---|---|
| `opioid_threshold` | Carries addiction risk; needs ethics review | `in_scope=false` |
| `eol_care_intensity` | Coercion risk at end of life; needs ethics review | `in_scope=false` |

The seed script inserts both with `in_scope=false` at the application layer.
Any attempt to create a `clinical_cases` row with one of these
`decision_class` values, or to create a `recommendations` row referencing
such a case, returns `409 Conflict: decision class not in MVP scope`.

## Audit-event taxonomy

Stable, finite list of `action` values written to `audit_events`:

```
auth.login
auth.login_failed
auth.logout
user.create
user.update
user.role_add
user.role_remove
patient.create
patient.update
patient.vitals_add
case.create
case.close
case.reopen
recommendation.create
recommendation.snapshot_added
recommendation.accept
recommendation.override
recommendation.escalate
recommendation.request_evidence
recommendation.elicit_submit
recommendation.resolve
recommendation.safety_flag
audit.export
```

The frontend never invents new `action` values; the backend enums them.

## Append-only enforcement

Postgres trigger (added by Alembic migration `0002_audit_append_only`):

```sql
CREATE OR REPLACE FUNCTION audit_events_no_modify()
RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'audit_events is append-only';
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_events_block_update
BEFORE UPDATE OR DELETE ON audit_events
FOR EACH ROW EXECUTE FUNCTION audit_events_no_modify();
```

For SQLite (dev), the equivalent is implemented at the SQLAlchemy session
layer — `AuditEvent` rows are inserted only via the audit service, which has
no `.update()` or `.delete()` method. The Alembic migration applies the
trigger only on Postgres; the service-layer guard covers SQLite.

## Override rationale

Every override requires a non-empty `rationale` (validated server-side, not
client-side). Overrides are recorded in `action_logs.action='override'` with
the rationale and feed into the eval-pipeline feedback row (reserved for
Phase 3 benchmark work).
