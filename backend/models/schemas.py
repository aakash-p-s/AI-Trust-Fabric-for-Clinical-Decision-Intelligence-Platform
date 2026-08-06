"""
backend/models/schemas.py
Canonical Pydantic schemas. Field names and shapes match PRD Section 9 exactly,
and must match data/patients.json, data/predictions.json, and
data/compliance_rulebook.json byte-for-byte in field names and types.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 9.1 PatientContext
# ---------------------------------------------------------------------------
class PatientContext(BaseModel):
    patient_id: str
    age: int
    symptoms: list[str]
    scan_type: str
    relevant_history: str


# ---------------------------------------------------------------------------
# 9.2 PredictionInput
# ---------------------------------------------------------------------------
class PredictionInput(BaseModel):
    model_config = {"protected_namespaces": ()}

    patient_id: str
    model_name: str
    model_version: str
    prediction: str  # e.g. 'PNEUMONIA', 'NORMAL'
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime


# ---------------------------------------------------------------------------
# 9.3 ComplianceRulebook
# ---------------------------------------------------------------------------
class ComplianceRulebook(BaseModel):
    approved_model_versions: list[str]
    minimum_confidence_threshold: float = Field(ge=0.0, le=1.0)
    high_risk_conditions_requiring_review: list[str]


class ComplianceRulebookUpdate(ComplianceRulebook):
    changed_by: str


# ---------------------------------------------------------------------------
# 9.4 DigitalTwin (response schema)
# ---------------------------------------------------------------------------
class ComplianceResult(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_version_approved: bool
    confidence_ok: bool
    high_risk_requires_review: bool
    flagged: bool
    flag_reasons: list[str]


class GroundedSource(BaseModel):
    id: str
    source: str
    similarity_score: float


class ReviewRecord(BaseModel):
    reviewed_by: str
    decision: Literal["approve", "override"]
    notes: str
    reviewed_at: datetime


class PredictionSummary(BaseModel):
    model_config = {"protected_namespaces": ()}

    label: str
    confidence: float
    model_version: str


class LineageRecord(BaseModel):
    model_config = {"protected_namespaces": ()}

    source: str
    input_captured_at: str
    patient_id: str
    model_version: str


class ExplainabilityCascadeAttempt(BaseModel):
    model_config = {"protected_namespaces": ()}

    model: str
    status: Literal["success", "failed"]
    reason: Optional[str] = None


class ExplainabilityCascade(BaseModel):
    model_config = {"protected_namespaces": ()}

    final_source: Literal["primary_llm", "fallback_llm", "deterministic_fallback"]
    model_used: Optional[str] = None
    attempts: list[ExplainabilityCascadeAttempt]
    token_usage: Optional[dict] = None
    duration_ms: int


class RagDetails(BaseModel):
    status: Literal["live", "degraded", "unavailable"]
    chunks_found: int
    top_similarity_score: float
    error: Optional[str] = None


class DigitalTwin(BaseModel):
    twin_id: str
    patient_id: str
    prediction: PredictionSummary
    lineage: LineageRecord
    compliance: ComplianceResult
    explanation: str
    explanation_type: Literal["narrative_llm_rag_grounded", "fallback_deterministic"]
    grounded_in_sources: list[GroundedSource]
    low_grounding_confidence: bool
    explanation_cascade: Optional[ExplainabilityCascade] = None
    rag_details: Optional[RagDetails] = None
    stage_durations_ms: Optional[dict] = None
    flagged: bool
    twin_created_at: datetime
    review: Optional[ReviewRecord] = None


class DigitalTwinDetail(DigitalTwin):
    patient: PatientContext


class TwinSummary(BaseModel):
    """Row shape used by GET /twins (Dashboard table)."""
    twin_id: str
    patient_id: str
    prediction: PredictionSummary
    flagged: bool
    review: Optional[ReviewRecord] = None
    twin_created_at: datetime


class TwinListResponse(BaseModel):
    total: int
    page: int
    limit: int
    twins: list[TwinSummary]


# ---------------------------------------------------------------------------
# Review request/response
# ---------------------------------------------------------------------------
class ReviewRequest(BaseModel):
    reviewer_username: str
    decision: Literal["approve", "override"]
    notes: str = ""


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


class UserPublic(BaseModel):
    username: str
    role: Literal["clinician", "compliance_governance"]
    display_name: str


class LoginResponse(BaseModel):
    success: bool
    user: Optional[UserPublic] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Rulebook changelog
# ---------------------------------------------------------------------------
class ChangelogEntry(BaseModel):
    changed_by: str
    change_description: str
    changed_at: datetime


class ChangelogResponse(BaseModel):
    entries: list[ChangelogEntry]


# ---------------------------------------------------------------------------
# Trust monitoring
# ---------------------------------------------------------------------------
class TrendPoint(BaseModel):
    date: str
    avg_confidence: Optional[float] = None
    pct_flagged: Optional[float] = None


class DriftAlert(BaseModel):
    id: str
    model_version: str
    alert_type: Literal["confidence_drop", "flag_rate_rise", "freshness_ok"]
    message: str
    severity: Literal["High", "Low"]
    status: Literal["Active", "Cleared"]
    detected_at: datetime


class TrustMonitoringSummary(BaseModel):
    confidence_trend: list[TrendPoint]
    flag_rate_trend: list[TrendPoint]
    avg_confidence_latest: float
    avg_confidence_delta_pct: float
    pct_flagged_latest: float
    pct_flagged_delta_pp: float
    total_predictions_in_range: int
    drift_status: Literal["Drift Detected", "Normal"]
    drift_since: Optional[str] = None


class TrustMonitoringRunNowResponse(TrustMonitoringSummary):
    new_alerts: list[DriftAlert] = []


class DriftAlertListResponse(BaseModel):
    alerts: list[DriftAlert]


# ---------------------------------------------------------------------------
# Dashboard summary
# ---------------------------------------------------------------------------
class DashboardSummary(BaseModel):
    total_predictions: int
    flagged_count: int
    flagged_pct: float
    avg_confidence: float
    active_drift_alerts: int


# ---------------------------------------------------------------------------
# AI Governance Assistant (chatbot)
# ---------------------------------------------------------------------------
class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatTurn] = []


class ChatResponse(BaseModel):
    reply: str
    tools_used: list[str] = []


# ---------------------------------------------------------------------------
# Governance page
# ---------------------------------------------------------------------------
class GovernanceSummary(BaseModel):
    total_processed: int
    avg_total_time_ms: float
    avg_explainability_ms: float
    total_tokens: int
    rag_live_rate_pct: float
    fallback_rate_pct: float


class PatientProcessingLogEntry(BaseModel):
    model_config = {"protected_namespaces": ()}

    twin_id: str
    patient_id: str
    stage_durations_ms: dict
    total_duration_ms: int
    rag_details: Optional[RagDetails] = None
    explanation_cascade: Optional[ExplainabilityCascade] = None
    flagged: bool
    review: Optional[ReviewRecord] = None
    twin_created_at: datetime


class PatientProcessingLogResponse(BaseModel):
    entries: list[PatientProcessingLogEntry]
