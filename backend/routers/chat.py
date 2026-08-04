"""
backend/routers/chat.py
POST /chat -- the AI Governance Assistant. Stateless: the frontend sends
the full conversation history with each request.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.models.schemas import ChatRequest, ChatResponse
from backend.routers.deps import get_db
from backend.services import audit_service, chat_agent_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    history = [turn.model_dump() for turn in payload.history]
    result = chat_agent_service.run_chat(payload.message, history)

    audit_service.write_audit_entry(
        db,
        entity_type="chat",
        entity_id="n/a",
        action="chat_message",
        actor="system",
        details={
            "message": payload.message,
            "tools_used": result["tools_used"],
        },
    )

    return ChatResponse(reply=result["reply"], tools_used=result["tools_used"])
