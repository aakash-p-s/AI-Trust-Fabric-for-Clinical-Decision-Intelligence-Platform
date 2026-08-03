"""
backend/db/models.py
SQLAlchemy ORM models. Dialect-agnostic -- works against PostgreSQL (default)
or SQLite (fallback, see .env.example). Tables match PRD Section 8 exactly.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import JSON

Base = declarative_base()


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# 8.1 patients
# ---------------------------------------------------------------------------
class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(String, primary_key=True)
    age = Column(Integer, nullable=False)
    symptoms = Column(JSON, nullable=False)  # list[str]
    scan_type = Column(String, nullable=False)
    relevant_history = Column(Text, nullable=False)


# ---------------------------------------------------------------------------
# 8.2 predictions
# ---------------------------------------------------------------------------
class PredictionRow(Base):
    __tablename__ = "predictions"

    id = Column(String, primary_key=True, default=_uuid)
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=False)
    model_name = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    prediction = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), default=_now)


# ---------------------------------------------------------------------------
# 8.3 digital_twins
# ---------------------------------------------------------------------------
class DigitalTwinRow(Base):
    __tablename__ = "digital_twins"

    twin_id = Column(String, primary_key=True, default=_uuid)
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=False)
    prediction = Column(JSON, nullable=False)  # {label, confidence, model_version}
    lineage = Column(JSON, nullable=False)
    compliance = Column(JSON, nullable=False)
    explanation = Column(Text, nullable=False)
    explanation_type = Column(String, nullable=False)
    grounded_in_sources = Column(JSON, nullable=False)  # list[{id, source, similarity_score}]
    low_grounding_confidence = Column(Boolean, nullable=False, default=False)
    flagged = Column(Boolean, nullable=False, default=False, index=True)
    twin_created_at = Column(DateTime(timezone=True), default=_now)
    review = Column(JSON, nullable=True)  # {reviewed_by, decision, notes, reviewed_at} | null


# ---------------------------------------------------------------------------
# 8.4 rulebook  (single row, id always 1)
# ---------------------------------------------------------------------------
class RulebookRow(Base):
    __tablename__ = "rulebook"

    id = Column(Integer, primary_key=True, default=1)
    approved_model_versions = Column(JSON, nullable=False)
    minimum_confidence_threshold = Column(Float, nullable=False)
    high_risk_conditions_requiring_review = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)


class RulebookChangelogRow(Base):
    __tablename__ = "rulebook_changelog"

    id = Column(Integer, primary_key=True, autoincrement=True)
    changed_by = Column(String, nullable=False)
    change_description = Column(Text, nullable=False)
    changed_at = Column(DateTime(timezone=True), default=_now)


# ---------------------------------------------------------------------------
# 8.5 drift_alerts
# ---------------------------------------------------------------------------
class DriftAlertRow(Base):
    __tablename__ = "drift_alerts"

    id = Column(String, primary_key=True, default=_uuid)
    model_version = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)  # confidence_drop | flag_rate_rise | freshness_ok
    message = Column(Text, nullable=False)
    severity = Column(String, nullable=False)  # High | Low
    status = Column(String, nullable=False, default="Active")  # Active | Cleared
    detected_at = Column(DateTime(timezone=True), default=_now)


# ---------------------------------------------------------------------------
# 8.6 audit_log  (append-only -- no UPDATE/DELETE statement may target this table)
# ---------------------------------------------------------------------------
class AuditLogRow(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String, nullable=False)  # 'twin' | 'rulebook' | 'review' | 'drift_alert'
    entity_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    details = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=_now)
