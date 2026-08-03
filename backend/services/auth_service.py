"""
backend/services/auth_service.py
Phase-1 authentication: a hardcoded username/password table, no JWT,
no Keycloak. See PRD Section 14 for the honest scope limitation.
"""
from typing import Optional

USERS = {
    "dr.mitchell": {
        "password": "clinician123",
        "role": "clinician",
        "display_name": "Dr. Sarah Mitchell",
    },
    "compliance.lead": {
        "password": "compliance123",
        "role": "compliance_governance",
        "display_name": "Compliance Team",
    },
}


def authenticate(username: str, password: str) -> Optional[dict]:
    user = USERS.get(username)
    if user and user["password"] == password:
        return {
            "username": username,
            "role": user["role"],
            "display_name": user["display_name"],
        }
    return None
