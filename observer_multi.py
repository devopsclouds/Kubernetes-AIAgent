import subprocess
import json


def get_all_pods(namespace):
    cmd = f"kubectl get pods -n {namespace} -o jsonpath='{{.items[*].metadata.name}}'"
    output = subprocess.getoutput(cmd).strip()
    return output.split() if output else []


def get_pod_raw_status(pod, namespace):
    cmd = f"kubectl get pod {pod} -n {namespace} -o json"
    raw = subprocess.getoutput(cmd)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "phase": "Unknown",
            "waiting_reason": None,
            "last_terminated_reason": None,
            "restart_count": 0,
        }

    container_statuses = data.get("status", {}).get("containerStatuses", [])

    waiting_reason = None
    last_terminated_reason = None
    restart_count = 0

    for cs in container_statuses:
        if cs.get("state", {}).get("waiting"):
            waiting_reason = cs["state"]["waiting"].get("reason")

        if cs.get("lastState", {}).get("terminated"):
            last_terminated_reason = cs["lastState"]["terminated"].get("reason")

        restart_count += cs.get("restartCount", 0)

    phase = data.get("status", {}).get("phase", "Unknown")

    return {
        "phase": phase,
        "waiting_reason": waiting_reason,
        "last_terminated_reason": last_terminated_reason,
        "restart_count": restart_count,
    }


def classify_pod_status(raw):
    waiting = raw["waiting_reason"]
    last = raw["last_terminated_reason"]
    phase = raw["phase"]
    restarts = raw["restart_count"]
 
    if waiting in ("ImagePullBackOff", "ErrImagePull"):
        return "ImagePullBackOff"
 
    if last == "OOMKilled":
        return "OOMKilled"
 
    if waiting == "CrashLoopBackOff":
        return "CrashLoopBackOff"
 
    if waiting == "CreateContainerConfigError":
        return "CreateContainerConfigError"
 
    if phase == "Running" and restarts > 0:
        return "RunningWithPriorRestarts"
 
    if phase == "Running":
        return "Running"
 
    if phase == "Pending":
        return "Pending"
 
    return "Unknown"
 

def get_pod_logs(pod, namespace, lines=100):
    return subprocess.getoutput(
        f"kubectl logs {pod} -n {namespace} --tail={lines}"
    )


def get_pod_events(pod, namespace):
    return subprocess.getoutput(
        f"kubectl describe pod {pod} -n {namespace}"
    )


def collect_context(pod, namespace):
    raw = get_pod_raw_status(pod, namespace)

    return {
        "pod": pod,
        "namespace": namespace,
        "status": classify_pod_status(raw),
        "raw_status": raw,
        "logs": get_pod_logs(pod, namespace),
        "events": get_pod_events(pod, namespace)
    }


def collect_all_contexts(namespace):
    pods = get_all_pods(namespace)
    return [collect_context(pod, namespace) for pod in pods]
