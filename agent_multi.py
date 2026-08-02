import time
import subprocess
import json

from observer_multi import collect_all_contexts
from llm_brain import llm_decide
from actions_multi import (
    restart_pod,
    scale_deployment,
    rollback_deployment,
    image_tag,
    bump_memory_limit,
    fix_pending_resources,
    get_container_name,
    notify
)

from config import (
    NAMESPACE,
    WAIT_TIME,
    KNOWN_GOOD_IMAGES,
    OOM_MEMORY_LIMIT,
    PENDING_MEMORY_REQUEST,
    PENDING_MEMORY_LIMIT,
    PENDING_CPU_REQUEST,
    PENDING_CPU_LIMIT
)

with open("prompts/incident_prompt.txt") as f:
    SYSTEM_PROMPT = f.read()


# ----------------------------
# Safe deterministic mapping
# ----------------------------
STATUS_ACTION_MAP = {
    "Running": "DO_NOTHING",
    "RunningWithPriorRestarts": "DO_NOTHING",
    "CrashLoopBackOff": "RESTART_POD",
    "ImagePullBackOff": "IMAGE_TAG",
    "CreateContainerConfigError": "ESCALATE_TO_HUMAN",
    "OOMKilled": "BUMP_MEMORY",
    "Pending": "FIX_PENDING",
}


# ----------------------------
# Retry protection
# ----------------------------
AUTO_REMEDIATION_HISTORY = {}
MAX_RESTART_ATTEMPTS = 1


# ----------------------------
# Suggestions engine
# ----------------------------
def get_suggestions(status):

    return {
        "CrashLoopBackOff": [
            "Check application logs",
            "Verify ConfigMap values",
            "Verify Secret values",
            "Check database connectivity",
            "Consider rollback deployment"
        ],

        "OOMKilled": [
            "Memory limit auto-increased - monitor for recurrence",
            "Check for memory leaks if OOM recurs after this fix",
            "Consider enabling HPA for sustained high load",
            "Review memory usage patterns over time"
        ],

        "ImagePullBackOff": [
            "Verify image exists in registry",
            "Check imagePullSecrets",
            "Verify Docker/ECR credentials",
            "Check image tag correctness",
            "Fix using: kubectl set image deployment/<name> <container>=<image>",
            "Rollback to previous version if needed"
        ],

        "CreateContainerConfigError": [
            "Validate ConfigMaps",
            "Validate Secrets",
            "Check environment variables"
        ],

        "Pending": [
            "Resource requests reduced automatically - monitor scheduling",
            "Check node capacity: kubectl describe nodes",
            "Consider adding more nodes or reducing replicas",
            "Check if PersistentVolumeClaim is unbound"
        ]

    }.get(status, ["Manual investigation required"])


# ----------------------------
# Deployment resolver
# ----------------------------
def get_deployment_name_for_pod(pod_name, namespace):

    try:
        pod_json = subprocess.getoutput(
            f"kubectl get pod {pod_name} -n {namespace} -o json"
        )

        pod_data = json.loads(pod_json)

        rs_name = None

        for owner in pod_data.get("metadata", {}).get("ownerReferences", []):
            if owner.get("kind") == "ReplicaSet":
                rs_name = owner.get("name")

        if rs_name:
            rs_json = subprocess.getoutput(
                f"kubectl get rs {rs_name} -n {namespace} -o json"
            )

            rs_data = json.loads(rs_json)

            for owner in rs_data.get("metadata", {}).get("ownerReferences", []):
                if owner.get("kind") == "Deployment":
                    return owner.get("name")

    except Exception:
        pass

    parts = pod_name.split("-")
    if len(parts) >= 3:
        return "-".join(parts[:-2])

    return pod_name


# ----------------------------
# Decision layer (LLM + rules)
# ----------------------------
def decide_action(context):

    status = context["status"]

    mapped_action = STATUS_ACTION_MAP.get(
        status,
        "ESCALATE_TO_HUMAN"
    )

    llm_result = llm_decide(
        context,
        SYSTEM_PROMPT
    )

    llm_action = None
    if isinstance(llm_result, dict):
        llm_action = llm_result.get("action")

    if llm_action and llm_action != mapped_action:
        notify(
            f"[{context['pod']}] LLM suggested {llm_action}, "
            f"using safe rule {mapped_action}"
        )

    # We NEVER trust LLM for execution
    return mapped_action


# ----------------------------
# Executor
# ----------------------------
def execute_action(action, context):

    pod = context["pod"]
    namespace = context["namespace"]

    deployment = get_deployment_name_for_pod(
        pod,
        namespace
    )

    if not deployment:
        notify(f"[{pod}] Could not resolve deployment")
        return


    # ---------------- CRASH LOOP ----------------
    if action == "RESTART_POD":

        attempts = AUTO_REMEDIATION_HISTORY.get(
            deployment,
            0
        )

        if attempts >= MAX_RESTART_ATTEMPTS:

            notify(
                f"[{pod}] Restart already attempted. Escalating."
            )

            for s in get_suggestions(context["status"]):
                notify(f"[{pod}] Suggestion: {s}")

            return

        notify(
            f"[{pod}] Restarting deployment {deployment}"
        )

        restart_pod(deployment, namespace)

        AUTO_REMEDIATION_HISTORY[deployment] = attempts + 1


    # ---------------- OOM KILLED (REAL FIX: BUMP MEMORY) ----------------
    elif action == "BUMP_MEMORY":

        container = get_container_name(deployment, namespace)

        notify(
            f"[{pod}] OOMKilled - increasing memory limit for "
            f"{deployment} (container: {container}) to {OOM_MEMORY_LIMIT}"
        )

        bump_memory_limit(
            deployment,
            namespace,
            container,
            new_limit=OOM_MEMORY_LIMIT
        )

        for s in get_suggestions(context["status"]):
            notify(f"[{pod}] Suggestion: {s}")


    # ---------------- PENDING (RESOURCE FIX) ----------------
    elif action == "FIX_PENDING":

        container = get_container_name(deployment, namespace)

        notify(
            f"[{pod}] Pending - fixing resource requests for "
            f"{deployment} (container: {container}) "
            f"mem={PENDING_MEMORY_LIMIT} cpu={PENDING_CPU_LIMIT}"
        )

        fix_pending_resources(
            deployment,
            namespace,
            container,
            memory_request=PENDING_MEMORY_REQUEST,
            memory_limit=PENDING_MEMORY_LIMIT,
            cpu_request=PENDING_CPU_REQUEST,
            cpu_limit=PENDING_CPU_LIMIT
        )

        for s in get_suggestions(context["status"]):
            notify(f"[{pod}] Suggestion: {s}")


    # ---------------- IMAGE PULL BACK OFF (AUTO FIX + SUGGEST) ----------------
    elif action == "IMAGE_TAG":

        notify(
            f"[{pod}] ImagePullBackOff detected → running auto recovery"
        )

        notify(
            f"[{pod}] If issue persists, run:"
        )

        notify(
            f"kubectl set image deployment/{deployment} "
            f"<container>=<correct-image> -n {namespace}"
        )

        notify(
            f"kubectl rollout restart deployment/{deployment} -n {namespace}"
        )

        notify(
            f"kubectl describe pod {pod} -n {namespace}"
        )

        for s in get_suggestions("ImagePullBackOff"):
            notify(f"[{pod}] Suggestion: {s}")

        known_good = KNOWN_GOOD_IMAGES.get(deployment)

        if known_good:
            notify(
                f"[{pod}] Applying configured known-good image: {known_good}"
            )
            image_tag(deployment, namespace, known_good)
        else:
            notify(
                f"[{pod}] No known-good image configured for "
                f"'{deployment}' - rolling back to previous revision instead"
            )
            rollback_deployment(deployment, namespace)


    # ---------------- DO NOTHING ----------------
    elif action == "DO_NOTHING":

        notify(f"[{pod}] Healthy - no action required")


    # ---------------- ESCALATE ----------------
    elif action == "ESCALATE_TO_HUMAN":

        notify(
            f"[{pod}] Escalation required: {context['status']}"
        )

        for s in get_suggestions(context["status"]):
            notify(f"[{pod}] Suggestion: {s}")


# ----------------------------
# Main loop
# ----------------------------
def main():

    notify("Incident Agent Started")

    contexts = collect_all_contexts(NAMESPACE)

    if not contexts:
        notify(f"No pods found in namespace {NAMESPACE}")
        return

    for context in contexts:

        notify(
            f"[{context['pod']}] Status: {context['status']}"
        )

        action = decide_action(context)

        notify(
            f"[{context['pod']}] Action: {action}"
        )

        execute_action(action, context)

    time.sleep(WAIT_TIME)

    notify("Incident sweep complete ✅")


if __name__ == "__main__":
    main()
