// Type definitions mirroring the backend Pydantic schemas.
// Keep in sync with backend/app/schemas/.

export type UUID = string;

export type RoutingDecision =
  | "answer"
  | "retrieve"
  | "elicit"
  | "escalate";

export type ConflictTypeLabel =
  | "evidence_gap_resolved"
  | "evidence_gap_checking"
  | "judgment_call"
  | "under_review";

export interface ElicitOption {
  id: string;
  label: string;
  description?: string;
}

export interface ReasoningStep {
  step: string;
  detail?: string;
  timestamp_ms?: number | null;
}

export interface EvidenceCitation {
  id: UUID;
  external_passage_id: string;
  source_body: string;
  document_title: string;
  section: string;
  evidence_grade: string;
  study_design: string;
  relevance_score: number;
  quality_score: number;
  excerpt: string;
}

export interface ReasoningSnapshot {
  id: UUID;
  model_version: string;
  routing_decision: RoutingDecision;
  conflict_label: ConflictTypeLabel;
  recommendation_text: string;
  primary_evidence_grade: string;
  confidence: number;
  tradeoff_statement: string | null;
  elicit_question: string | null;
  elicit_options: ElicitOption[];
  escalation_reason: string | null;
  identifiability_flag: boolean;
  uncertainty_decomposition: Record<string, number>;
  safety_verdict: string;
  safety_issues: string[];
  reasoning_trail: ReasoningStep[];
  latency_ms: number;
  sequence_number: number;
  created_at: string;
}

export interface RecommendationResponse {
  id: UUID;
  case_id: UUID;
  state: string;
  final_recommendation_text: string | null;
  final_rationale: string | null;
  decided_at: string | null;
  created_at: string;
  latest_snapshot_id: UUID | null;
  snapshot: ReasoningSnapshot | null;
  citations: EvidenceCitation[];
}

export interface RecommendationListItem {
  id: UUID;
  case_id: UUID;
  state: string;
  created_at: string;
  decided_at: string | null;
}

export interface CaseListItem {
  id: UUID;
  patient_id: UUID;
  doctor_id: UUID;
  senior_reviewer_id: UUID | null;
  decision_class: string;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface CaseResponse extends CaseListItem {
  closed_at: string | null;
}

export interface PatientSummary {
  id: UUID;
  display_name: string;
  external_mrn: string | null;
  created_at: string;
}

export interface PatientDetail extends PatientSummary {
  demographics: {
    dob: string | null;
    sex: string | null;
    ethnicity: string | null;
  };
  conditions: Array<{
    id: string;
    icd10_code: string | null;
    label: string;
    onset_date: string | null;
    status: string;
  }>;
  medications: Array<{
    id: string;
    rxnorm_code: string | null;
    label: string;
    dose: string | null;
    started_at: string | null;
    stopped_at: string | null;
  }>;
  allergies: Array<{
    id: string;
    substance: string;
    reaction: string | null;
    severity: string;
  }>;
  vitals: Array<{
    id: string;
    recorded_at: string;
    systolic_bp: number | null;
    diastolic_bp: number | null;
    hr: number | null;
    spo2: number | null;
    temp_c: number | null;
    glucose_mg_dl: number | null;
    notes: string | null;
  }>;
}

export interface DecisionClass {
  decision_class: string;
  display_label: string;
  in_scope: boolean;
  requires_ethics_review: boolean;
  notes: string;
}

export interface AuditEvent {
  id: UUID;
  actor_user_id: UUID | null;
  action: string;
  target_type: string;
  target_id: UUID | null;
  occurred_at: string;
  ip: string | null;
  user_agent: string | null;
  payload_json: string;
}

export interface ModelVersionUsage {
  model_version_id: UUID;
  provider: string;
  name: string;
  is_active: boolean;
  recommendation_count: number;
}

export interface User {
  id: UUID;
  email: string;
  full_name: string;
  roles: string[];
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface ActionResponse {
  recommendation_id: UUID;
  state: string;
  decided_at: string | null;
  final_recommendation_text: string | null;
  final_rationale: string | null;
}
