from openai import OpenAI
from config import ALLOWED_ACTIONS

client = OpenAI()

def llm_decide(context, system_prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""
Pod status: {context['status']}

Logs:
{context['logs']}
"""
            }
        ],
        temperature=0
    )

    decision = response.choices[0].message.content.strip()

    if decision not in ALLOWED_ACTIONS:
        return "ESCALATE_TO_HUMAN"

    return decision
