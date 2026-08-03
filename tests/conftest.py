"""
tests/conftest.py
Shared pytest fixtures. Uses an in-memory SQLite database for tests --
the ORM models are dialect-agnostic (PRD Section 8), so this is a valid
substitute for Postgres in automated tests.
"""
import json
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.db.models import Base, Patient, RulebookRow  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture()
def db_session():
    # StaticPool is required here: without it, each new connection checked out
    # from the pool (e.g. from a different thread, as TestClient uses) gets its
    # own *separate* SQLite in-memory database, causing "no such table" errors.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # seed patients + rulebook so tests can exercise the full API surface
    with open(DATA_DIR / "patients.json") as f:
        for p in json.load(f):
            session.add(Patient(**p))
    with open(DATA_DIR / "compliance_rulebook.json") as f:
        rb = json.load(f)
        session.add(RulebookRow(id=1, **rb))
    session.commit()

    yield session
    session.close()


@pytest.fixture()
def rulebook_dict():
    with open(DATA_DIR / "compliance_rulebook.json") as f:
        return json.load(f)


@pytest.fixture()
def sample_prediction():
    with open(DATA_DIR / "predictions.json") as f:
        preds = json.load(f)
    return next(p for p in preds if p["patient_id"] == "P0009")


@pytest.fixture()
def sample_patient():
    with open(DATA_DIR / "patients.json") as f:
        patients = json.load(f)
    return next(p for p in patients if p["patient_id"] == "P0009")
