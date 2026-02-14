import subprocess

def get_pod_status(pod, namespace):
    reason_cmd = (
        f"kubectl get pod {pod} -n {namespace} "
        "-o jsonpath='{.status.containerStatuses[0].state.waiting.reason}'"
    )

    reason = subprocess.getoutput(reason_cmd)

    if "CrashLoopBackOff" in reason:
        return "CrashLoopBackOff"

    phase_cmd = (
        f"kubectl get pod {pod} -n {namespace} "
        "-o jsonpath='{.status.phase}'"
    )

    return subprocess.getoutput(phase_cmd)

def get_pod_logs(pod, namespace, lines=50):
    cmd = f"kubectl logs {pod} -n {namespace} --tail={lines}"
    return subprocess.getoutput(cmd)

def collect_context(pod, namespace):
    return {
        "pod": pod,
        "namespace": namespace,
        "status": get_pod_status(pod, namespace),
        "logs": get_pod_logs(pod, namespace)[:1000]
    }
