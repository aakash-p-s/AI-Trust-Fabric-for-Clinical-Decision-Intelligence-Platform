"""
backend/routers/deps.py

Shared FastAPI dependencies.

IMPORTANT / HONEST LIMITATION (see PRD Section 14.3):
require_role() reads the X-User-Role header, which the frontend sets from
whatever was returned by POST /auth/login. This is NOT cryptographically
secure -- nothing here is signed, so a client could in principle send any
X-User-Role value it wants. This is an explicit, documented simplification
for phase 1 (no JWT, no Keycloak). The direct upgrade path is listed in
PRD Section 20 (Future Extension Points).
"""
from fastapi import Header, HTTPException

from backend.db.session import get_db  # re-exported for convenience

__all__ = ["get_db", "require_role"]


def require_role(required_role: str):
    def _dependency(x_user_role: str = Header(default="")):
        if x_user_role != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Only {required_role} may perform this action.",
            )
        return x_user_role

    return _dependency
