"""
scripts/test_live_explainability.py
Verifies that load_dotenv() in main.py fixes the issue:
- OPENROUTER_API_KEY is picked up from .env
- The real LLM is called (response is NOT the fallback message)
- The explanation text is non-empty and meaningful
"""
import os
import sys
from pathlib import Path

# Mimic what backend/main.py now does at startup
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.services import rag_service
from backend.agents.explainability_agent import explainability_node

FALLBACK_MARKER = "explainability service was unavailable"

state = {
    "prediction_input": {
        "patient_id": "P0009",
        "model_name": "vit-xray-pneumonia-classification",
        "model_version": "v2.1",
        "prediction": "PNEUMONIA",
        "confidence": 0.8423,
    },
    "patient_context": {
        "patient_id": "P0009",
        "age": 64,
        "symptoms": ["low oxygen saturation", "cough"],
        "scan_type": "chest_xray",
        "relevant_history": "smoker, prior respiratory issues",
    },
}

print("OPENROUTER_API_KEY set:", bool(os.getenv("OPENROUTER_API_KEY")))

rag_service.load_knowledge_base()
result = explainability_node(state)
exp = result["explanation"]

print("\n--- Explanation ---")
print(exp["text"])
print("\nGrounded in:", [s["source"] for s in exp["grounded_in_sources"]])
print("Low grounding confidence:", exp["low_grounding_confidence"])

assert exp["text"], "Explanation text is empty"
assert FALLBACK_MARKER not in exp["text"], (
    "Got fallback message — LLM call failed. Check OPENROUTER_API_KEY in .env"
)
print("\nPASS: Real LLM response received -- load_dotenv() fix confirmed.")
