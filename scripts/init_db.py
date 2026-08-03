"""
scripts/init_db.py
Creates all tables defined in backend/db/models.py. Safe to re-run
(create_all is idempotent -- it never drops or alters existing tables).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.db.models import Base  # noqa: E402
from backend.db.session import engine  # noqa: E402


def main():
    Base.metadata.create_all(bind=engine)
    print("All tables created (or already existed).")


if __name__ == "__main__":
    main()
