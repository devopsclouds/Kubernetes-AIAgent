import time
from observer import collect_context, get_pod_status
from llm_brain import llm_decide
from actions import restart_pod, scale_deployment, notify
from config import (
    POD_NAME,
    NAMESPACE,
    DEPLOYMENT_NAME,
    WAIT_TIME
)

with open("prompts/incident_prompt.txt") as f:
    SYSTEM_PROMPT = f.read()

def execute_action(action):
    if action == "RESTART_POD":
        restart_pod(DEPLOYMENT_NAME, NAMESPACE)

    elif action == "SCALE_DEPLOYMENT":
        scale_deployment(DEPLOYMENT_NAME, NAMESPACE)

    elif action == "DO_NOTHING":
        notify("No action required")

    elif action == "ESCALATE_TO_HUMAN":
        notify("Escalating incident to human")

def main():
    notify("Incident Agent Started")

    context = collect_context(POD_NAME, NAMESPACE)
    notify(f"Pod Status: {context['status']}")

    action = llm_decide(context, SYSTEM_PROMPT)
    notify(f"LLM Decision: {action}")

    execute_action(action)

    time.sleep(WAIT_TIME)

    notify("Incident resolved successfully ✅")

if __name__ == "__main__":
    main()