"""Mock reasoning provider — produces the four routing-decision outcomes.

Deterministic per case id. Reads from `seeded_cases.json`. Simulates latency
(200–800 ms) so loading states render realistically. Re-evaluation after a
`RETRIEVE` state advances the same case to `ANSWER` on the next call
(timer-based), so the polling workflow is demonstrable end-to-end.

This provider is the only thing standing in for CARMA until Phase 2.
"""
from __future__ import annotations

import json
import random
import time
from pathlib import Path
from uuid import UUID

from app.services.reasoning.provider import (
    EvidenceCitation,
    ReasoningRequest,
    ReasoningResponse,
    ReasoningStep,
)
from app.services.reasoning.states import (
    CONFLICT_LABEL_FOR_ROUTING,
    ConflictTypeLabel,
    RoutingDecision,
    routing_from_str,
)

_SEEDED_PATH = Path(__file__).parent / "seeded_cases.json"
MODEL_VERSION_NAME = "mock-v0.1.0"

# Stable random seed per case so demo runs are reproducible per case id.
_STABLE_SEED = 0xC0FFEE


def _load_seeded_cases() -> dict:
    with _SEEDED_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


_SEEDED = _load_seeded_cases()
_CASES_BY_ID: dict[str, dict] = {c["case_id"]: c for c in _SEEDED["cases"]}


# Routing keyed by decision_class when no seeded case_id matches. This
# makes the demo deterministic for *any* case whose decision_class is one
# of the seeded ones. New (unseeded) decision_classes fall back to `answer`.
_ROUTING_BY_DECISION_CLASS: dict[str, str] = {
    "statin_initiation_qrisk_vs_acc_aha": "answer",
    "anticoagulation_af_chadsvasc": "retrieve_then_answer",
    "bp_target_jnc8_vs_acc_aha_2017": "elicit",
    "psa_screening_uspstf_vs_aua": "escalate",
    "hba1c_target": "answer",
    "egfr_drug_cutoff": "answer",
}


class MockReasoningProvider:
    """Deterministic mock provider keyed by case_id, falling back to
    decision_class for newly-created cases."""

    name = "mock"

    def reason(self, request: ReasoningRequest) -> ReasoningResponse:
        started = time.perf_counter()

        case_id_str = str(request.case_id)
        seeded = _CASES_BY_ID.get(case_id_str)

        # If a prior snapshot exists and the request is a re-evaluation,
        # advance `RETRIEVE` -> `ANSWER` deterministically (regardless of
        # which case produced it).
        if request.prior_snapshot_id is not None:
            followup_seed = seeded or {
                "decision_class": request.decision_class,
                "title": "follow-up",
            }
            return self._build_retrieve_followup(followup_seed, request, started)

        # Unseeded case id but seeded decision_class -> use the routing map.
        if seeded is None:
            if request.decision_class not in _ROUTING_BY_DECISION_CLASS:
                return self._build_unknown_response(request, started)
            routing_str = _ROUTING_BY_DECISION_CLASS[request.decision_class]
            synthetic = {"decision_class": request.decision_class, "title": "case"}
        else:
            routing_str = seeded.get("expected_routing", "answer")
            synthetic = seeded

        if routing_str == "retrieve_then_answer":
            return self._build_retrieve(synthetic, request, started)

        routing = routing_from_str(routing_str)
        if routing == RoutingDecision.ELICIT:
            return self._build_elicit(synthetic, request, started)
        if routing == RoutingDecision.ESCALATE:
            return self._build_escalate(synthetic, request, started)
        return self._build_answer(synthetic, request, started)

    # ── Builders ─────────────────────────────────────────────────────────

    def _build_unknown_response(
        self, request: ReasoningRequest, started: float
    ) -> ReasoningResponse:
        return ReasoningResponse(
            routing=RoutingDecision.ANSWER,
            conflict_label=CONFLICT_LABEL_FOR_ROUTING[RoutingDecision.ANSWER],
            recommendation_text=(
                "No benchmark case matches this case id. Defaulting to a "
                "generic 'consult local protocol' recommendation."
            ),
            primary_evidence_grade="low",
            confidence=0.40,
            uncertainty_decomposition={"insufficient": 0.6},
            evidence_citations=[],
            reasoning_trail=[
                ReasoningStep(step="mock_default", detail="unseeded case id"),
            ],
            model_version_name=MODEL_VERSION_NAME,
            latency_ms=(time.perf_counter() - started) * 1000,
        )

    def _build_answer(
        self, seeded: dict, request: ReasoningRequest, started: float
    ) -> ReasoningResponse:
        rand = random.Random(_STABLE_SEED ^ hash(request.case_id))
        body = _answer_body(seeded)
        return ReasoningResponse(
            routing=RoutingDecision.ANSWER,
            conflict_label=CONFLICT_LABEL_FOR_ROUTING[RoutingDecision.ANSWER],
            recommendation_text=body,
            primary_evidence_grade="moderate",
            confidence=round(0.78 + rand.uniform(-0.05, 0.05), 3),
            uncertainty_decomposition={"resolvable": 0.7, "irreducible": 0.3},
            evidence_citations=_default_citations(seeded),
            reasoning_trail=[
                ReasoningStep(step="evidence_retrieved", detail="3 passages"),
                ReasoningStep(step="concordance_scored", detail="weighted mean 0.71"),
                ReasoningStep(
                    step="edc_computed",
                    detail="λ₁ / Σ|λ_k| = 0.78 (mock)",
                ),
                ReasoningStep(
                    step="conflict_resolved",
                    detail=seeded.get("rationale", ""),
                ),
            ],
            model_version_name=MODEL_VERSION_NAME,
            latency_ms=(time.perf_counter() - started) * 1000,
        )

    def _build_retrieve(
        self, seeded: dict, request: ReasoningRequest, started: float
    ) -> ReasoningResponse:
        rand = random.Random(_STABLE_SEED ^ hash(request.case_id))
        return ReasoningResponse(
            routing=RoutingDecision.RETRIEVE,
            conflict_label=CONFLICT_LABEL_FOR_ROUTING[RoutingDecision.RETRIEVE],
            recommendation_text="Checking one more source before answering.",
            primary_evidence_grade="moderate",
            confidence=round(0.55 + rand.uniform(-0.05, 0.05), 3),
            uncertainty_decomposition={"insufficient": 0.55, "resolvable": 0.45},
            evidence_citations=_default_citations(seeded)[:1],
            reasoning_trail=[
                ReasoningStep(
                    step="evpi_check",
                    detail="Δ expected utility with retrieval > threshold",
                ),
                ReasoningStep(
                    step="retrieval_in_progress",
                    detail="querying one more passage (renal dosing)",
                ),
            ],
            model_version_name=MODEL_VERSION_NAME,
            retrieval_trace_id=f"mock-{request.case_id}-1",
            latency_ms=(time.perf_counter() - started) * 1000,
        )

    def _build_retrieve_followup(
        self, seeded: dict, request: ReasoningRequest, started: float
    ) -> ReasoningResponse:
        rand = random.Random(_STABLE_SEED ^ hash(request.case_id) ^ 0x02)
        return ReasoningResponse(
            routing=RoutingDecision.ANSWER,
            conflict_label=CONFLICT_LABEL_FOR_ROUTING[RoutingDecision.ANSWER],
            recommendation_text=_answer_body_followup(seeded),
            primary_evidence_grade="high",
            confidence=round(0.82 + rand.uniform(-0.05, 0.05), 3),
            uncertainty_decomposition={"resolvable": 0.85, "irreducible": 0.15},
            evidence_citations=_default_citations(seeded),
            reasoning_trail=[
                ReasoningStep(step="retrieval_followup", detail="1 additional passage"),
                ReasoningStep(step="concordance_rescored", detail="weighted mean 0.84"),
                ReasoningStep(step="conflict_resolved", detail="epistemic gap closed"),
            ],
            model_version_name=MODEL_VERSION_NAME,
            retrieval_trace_id=f"mock-{request.case_id}-2",
            latency_ms=(time.perf_counter() - started) * 1000,
        )

    def _build_elicit(
        self, seeded: dict, request: ReasoningRequest, started: float
    ) -> ReasoningResponse:
        rand = random.Random(_STABLE_SEED ^ hash(request.case_id))
        return ReasoningResponse(
            routing=RoutingDecision.ELICIT,
            conflict_label=CONFLICT_LABEL_FOR_ROUTING[RoutingDecision.ELICIT],
            recommendation_text=(
                "The guidelines disagree on the BP target for this patient. "
                "This is a judgment call."
            ),
            primary_evidence_grade="moderate",
            confidence=0.0,
            uncertainty_decomposition={"irreducible": 0.85, "insufficient": 0.15},
            tradeoff_statement=(
                "Option A (JNC8): target 140/90 mmHg — slightly higher, fewer "
                "medications, less risk of symptomatic hypotension.\n"
                "Option B (ACC/AHA 2017): target 130/80 mmHg — tighter control, "
                "lower stroke risk per SPRINT, more medications and monitoring."
            ),
            elicit_question=(
                "Which tradeoff matters more for this patient given their "
                "diabetes, current readings, and tolerance for additional "
                "medication burden?"
            ),
            elicit_options=[
                {
                    "id": "loose_target",
                    "label": "Prefer a looser target (140/90)",
                    "description": (
                        "Fewer medications, prioritize tolerability and adherence."
                    ),
                },
                {
                    "id": "tight_target",
                    "label": "Prefer a tighter target (130/80)",
                    "description": (
                        "Lower stroke risk; accept additional medication burden."
                    ),
                },
                {
                    "id": "patient_choice",
                    "label": "Let the patient decide after conversation",
                    "description": (
                        "Document shared decision-making and revisit in 4 weeks."
                    ),
                },
            ],
            evidence_citations=_default_citations(seeded),
            reasoning_trail=[
                ReasoningStep(
                    step="conflict_typed",
                    detail="irreducible uncertainty > threshold",
                ),
                ReasoningStep(
                    step="tradeoff_surfaced",
                    detail="two distinct normative recommendations",
                ),
            ],
            model_version_name=MODEL_VERSION_NAME,
            latency_ms=(time.perf_counter() - started) * 1000,
        )

    def _build_escalate(
        self, seeded: dict, request: ReasoningRequest, started: float
    ) -> ReasoningResponse:
        return ReasoningResponse(
            routing=RoutingDecision.ESCALATE,
            conflict_label=ConflictTypeLabel.UNDER_REVIEW,
            recommendation_text=(
                "This case cannot be confidently classified as epistemic or "
                "normative. Routing to senior clinical review."
            ),
            primary_evidence_grade="low",
            confidence=0.30,
            uncertainty_decomposition={"insufficient": 0.6, "irreducible": 0.4},
            escalation_reason=(
                "Non-identifiable conflict — atypical presentation under "
                "immunosuppression context; mixed guideline signals."
            ),
            identifiability_flag=False,
            evidence_citations=_default_citations(seeded)[:1],
            reasoning_trail=[
                ReasoningStep(step="rpd_check", detail="identifiability=false"),
                ReasoningStep(
                    step="escalation_routed",
                    detail="senior clinician review queue",
                ),
            ],
            model_version_name=MODEL_VERSION_NAME,
            latency_ms=(time.perf_counter() - started) * 1000,
        )


def _answer_body(seeded: dict) -> str:
    dc = seeded.get("decision_class", "")
    if dc == "statin_initiation_qrisk_vs_acc_aha":
        return (
            "Initiate moderate-intensity statin (atorvastatin 20 mg daily). "
            "ACC/AHA pooled cohort equations estimate 10-year ASCVD risk "
            "above the 7.5% threshold; QRISK3 borderline but consistent at "
            "this age-band. Re-check lipid panel in 12 weeks."
        )
    if dc == "hba1c_target":
        return (
            "Target HbA1c 7.5%. ACCORD/ADVANCE/UKPDS converge for adults "
            "over 50 with CKD stage 3a. Avoid tighter targets given CKD — "
            "risk of hypoglycemia outweighs marginal microvascular benefit."
        )
    if dc == "egfr_drug_cutoff":
        return (
            "Initiate SGLT2 inhibitor (empagliflozin 10 mg daily). KDIGO "
            "2023 update supersedes FDA labelling for this eGFR band — "
            "renal and cardiovascular benefit established in CREDENCE/DAPA-CKD."
        )
    return f"Mock recommendation for {seeded.get('title', 'unknown case')}."


def _answer_body_followup(seeded: dict) -> str:
    if seeded.get("decision_class") == "anticoagulation_af_chadsvasc":
        return (
            "Initiate apixaban 2.5 mg BID. CHA2DS2-VASc=2 with CKD stage 3a "
            "meets ESC criteria; renal-dosed apixaban preferred over warfarin "
            "given age >70 and bleeding risk per HAS-BLED."
        )
    return _answer_body(seeded)


def _default_citations(seeded: dict) -> list[EvidenceCitation]:
    base = seeded.get("decision_class", "general")
    titles = {
        "statin_initiation_qrisk_vs_acc_aha": [
            ("AHA", "2019 ACC/AHA Guideline on Primary Prevention", "Statin Eligibility"),
            ("NICE", "NG238 Lipid Management", "QRISK3 Threshold"),
        ],
        "anticoagulation_af_chadsvasc": [
            ("ESC", "2020 AF Guidelines", "Anticoagulation Initiation"),
            ("ACC/AHA", "2023 AF Guideline Focused Update", "Renal Dosing"),
        ],
        "bp_target_jnc8_vs_acc_aha_2017": [
            ("JNC8", "2014 Hypertension Guideline", "Target in Adults"),
            ("ACC/AHA", "2017 Hypertension Guideline", "SPRINT Subgroup"),
        ],
        "psa_screening_uspstf_vs_aua": [
            ("USPSTF", "2018 PSA Recommendation", "Screening Interval"),
            ("AUA", "Prostate Cancer Early Detection", "Shared Decision"),
        ],
        "hba1c_target": [
            ("ACCORD", "Glycemic Control Trial", "Tight Target Outcome"),
            ("ADVANCE", "Intensive Glucose Control", "CKD Subgroup"),
        ],
        "egfr_drug_cutoff": [
            ("KDIGO", "2023 CKD Guideline", "SGLT2 Initiation"),
            ("FDA", "SGLT2 Label", "eGFR Cutoff"),
        ],
    }
    pairs = titles.get(base, [("Cochrane", "General Review", "Summary")])
    return [
        EvidenceCitation(
            external_passage_id=f"passage-{base}-{i}",
            source_body=body,
            document_title=title,
            section=section,
            evidence_grade="moderate",
            study_design="guideline",
            relevance_score=0.7 - i * 0.05,
            quality_score=0.65 - i * 0.04,
            excerpt=(
                f"Excerpt from {title} — {section}: guidelines recommend ..."
            ),
        )
        for i, (body, title, section) in enumerate(pairs)
    ]


def load_seeded_decision_classes() -> list[dict]:
    return list(_SEEDED.get("decision_classes", []))
