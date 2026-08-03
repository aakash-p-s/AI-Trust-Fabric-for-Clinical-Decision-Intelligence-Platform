export type Role = "clinician" | "compliance_governance";

export interface User {
  username: string;
  role: Role;
  display_name: string;
}

export interface PredictionSummary {
  label: string;
  confidence: number;
  model_version: string;
}

export interface LineageRecord {
  source: string;
  input_captured_at: string;
  patient_id: string;
  model_version: string;
}

export interface ComplianceResult {
  model_version_approved: boolean;
  confidence_ok: boolean;
  high_risk_requires_review: boolean;
  flagged: boolean;
  flag_reasons: string[];
}

export interface GroundedSource {
  id: string;
  source: string;
  similarity_score: number;
}

export interface ReviewRecord {
  reviewed_by: string;
  decision: "approve" | "override";
  notes: string;
  reviewed_at: string;
}

export interface PatientContext {
  patient_id: string;
  age: number;
  symptoms: string[];
  scan_type: string;
  relevant_history: string;
}

export interface TwinSummary {
  twin_id: string;
  patient_id: string;
  prediction: PredictionSummary;
  flagged: boolean;
  twin_created_at: string;
}

export interface DigitalTwin {
  twin_id: string;
  patient_id: string;
  prediction: PredictionSummary;
  lineage: LineageRecord;
  compliance: ComplianceResult;
  explanation: string;
  explanation_type: string;
  grounded_in_sources: GroundedSource[];
  low_grounding_confidence: boolean;
  flagged: boolean;
  twin_created_at: string;
  review: ReviewRecord | null;
}

export interface DigitalTwinDetail extends DigitalTwin {
  patient: PatientContext;
}

export interface TwinListResponse {
  total: number;
  page: number;
  limit: number;
  twins: TwinSummary[];
}

export interface ComplianceRulebook {
  approved_model_versions: string[];
  minimum_confidence_threshold: number;
  high_risk_conditions_requiring_review: string[];
}

export interface ChangelogEntry {
  changed_by: string;
  change_description: string;
  changed_at: string;
}

export interface TrendPoint {
  date: string;
  avg_confidence?: number;
  pct_flagged?: number;
}

export interface DriftAlert {
  id: string;
  model_version: string;
  alert_type: "confidence_drop" | "flag_rate_rise" | "freshness_ok";
  message: string;
  severity: "High" | "Low";
  status: "Active" | "Cleared";
  detected_at: string;
}

export interface TrustMonitoringSummary {
  confidence_trend: TrendPoint[];
  flag_rate_trend: TrendPoint[];
  avg_confidence_latest: number;
  avg_confidence_delta_pct: number;
  pct_flagged_latest: number;
  pct_flagged_delta_pp: number;
  total_predictions_in_range: number;
  drift_status: "Drift Detected" | "Normal";
  drift_since: string | null;
}

export interface DashboardSummary {
  total_predictions: number;
  flagged_count: number;
  flagged_pct: number;
  avg_confidence: number;
  active_drift_alerts: number;
}
