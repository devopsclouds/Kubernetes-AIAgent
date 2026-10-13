import requests
import json
from config import ALLOWED_ACTIONS

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"


def llm_decide(context, system_prompt):

    prompt = f"""
{system_prompt}

You are a Kubernetes SRE assistant.

Analyze incident and return JSON ONLY:

{{
  "analysis": "short root cause",
  "recommendations": [
    "step 1",
    "step 2",
    "step 3"
  ]
}}

Pod: {context['pod']}
Status: {context['status']}
Logs: {context['logs'][:2000]}
Events: {context.get('events','')[:2000]}
"""

    try:
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
        raw = result.get("response", "").strip()

        return json.loads(raw)

    except Exception:
        return {
            "analysis": "LLM failed",
            "recommendations": []
        }
