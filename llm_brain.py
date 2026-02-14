import requests
from config import ALLOWED_ACTIONS

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"

def llm_decide(context, system_prompt):
    prompt = f"""
{system_prompt}

Pod status:
{context['status']}

Logs:
{context['logs']}

Return ONLY one action from:
{", ".join(ALLOWED_ACTIONS)}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=60
    )

    result = response.json()
    decision = result.get("response", "").strip()

    if decision not in ALLOWED_ACTIONS:
        return "ESCALATE_TO_HUMAN"

    return decision
