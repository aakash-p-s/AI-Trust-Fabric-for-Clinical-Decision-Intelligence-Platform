"""
backend/services/chat_agent_service.py
The AI Governance Assistant's reasoning loop: standard LangChain
tool-calling pattern.
"""
import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from backend.services.chat_tools import ALL_TOOLS, TOOLS_BY_NAME

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 4

SYSTEM_PROMPT = """You are the AI Governance Assistant for the Autonomous AI \
Trust Fabric platform, a healthcare AI compliance and audit system.

You help Compliance/Governance staff and clinicians understand:
- Why a specific patient's AI prediction was made or flagged
- Which patients currently need review
- What the current compliance rulebook says
- Trust monitoring health: confidence trends, drift, alerts

CRITICAL RULES:
- You have NO knowledge of any patient, prediction, or rule except what a \
tool call actually returns. NEVER state a fact about a patient, twin, or \
the rulebook unless you retrieved it via a tool in this conversation.
- If a tool returns an error (e.g. patient not found), say so plainly -- \
do not guess or make up a plausible-sounding answer.
- If a question is outside this system's data (patients, predictions, \
compliance, trust monitoring), say you can only help with those topics.
- Keep answers concise and clinical-audience-appropriate: plain English, \
no unnecessary hedging, cite specific numbers/reasons from tool results \
rather than vague summaries.
"""


def _history_to_messages(history):
    messages = []
    for turn in history:
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        elif turn["role"] == "assistant":
            messages.append(AIMessage(content=turn["content"]))
    return messages


def run_chat(message, history=None):
    """Returns {"reply": str, "tools_used": list[str]}."""
    from backend.llm_config import llm_chat_assistant

    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    messages.extend(_history_to_messages(history or []))
    messages.append(HumanMessage(content=message))

    llm_with_tools = llm_chat_assistant.bind_tools(ALL_TOOLS)
    tools_used = []

    for iteration in range(MAX_TOOL_ITERATIONS):
        try:
            response = llm_with_tools.invoke(messages)
        except Exception as exc:  # noqa: BLE001
            logger.error("[chat_agent] LLM call failed: %s", exc)
            return {
                "reply": "I'm having trouble reaching the assistant service right now. Please try again shortly.",
                "tools_used": tools_used,
            }

        messages.append(response)
        tool_calls = getattr(response, "tool_calls", None) or []

        if not tool_calls:
            return {"reply": response.content, "tools_used": tools_used}

        for tool_call in tool_calls:
            tool_fn = TOOLS_BY_NAME.get(tool_call["name"])
            if tool_fn is None:
                tool_result = {"error": "Unknown tool '%s'" % tool_call["name"]}
            else:
                try:
                    tool_result = tool_fn.invoke(tool_call["args"])
                except Exception as exc:  # noqa: BLE001
                    tool_result = {"error": "Tool execution failed: %s" % exc}
                tools_used.append(tool_call["name"])

            messages.append(
                ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"])
            )

    logger.warning("[chat_agent] Hit MAX_TOOL_ITERATIONS without a final answer")
    return {
        "reply": "I wasn't able to fully answer that within my available steps -- "
        "could you rephrase, or ask about one thing at a time?",
        "tools_used": tools_used,
    }
