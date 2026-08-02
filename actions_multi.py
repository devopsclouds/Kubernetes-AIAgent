import subprocess
import time


# ----------------------------
# Simple safe logger (NO imports from other modules)
# ----------------------------
def notify(msg):
    print(msg)


# ----------------------------
# Restart Deployment
# ----------------------------
def restart_pod(deployment, namespace):

    notify(f"[ACTION] Restarting deployment: {deployment}")

    cmd = (
        f"kubectl rollout restart deployment/{deployment} "
        f"-n {namespace}"
    )

    subprocess.run(cmd, shell=True)

    time.sleep(2)

# ----------------------------
# Fix Pending pod — reduce resource requests so scheduler can place it
# ----------------------------
def fix_pending_resources(deployment, namespace, container,
                           memory_request, memory_limit,
                           cpu_request, cpu_limit):

    notify(f"[ACTION] Fixing pending resources: {deployment} "
           f"(container: {container}) → mem={memory_limit} cpu={cpu_limit}")

    cmd = (
        f"kubectl set resources deployment/{deployment} "
        f"-c {container} "
        f"--requests=memory={memory_request},cpu={cpu_request} "
        f"--limits=memory={memory_limit},cpu={cpu_limit} "
        f"-n {namespace}"
    )

    subprocess.run(cmd, shell=True)

    time.sleep(2)

#----------------------
# Resolve the real container name (don't assume it == deployment name)
# ----------------------------
def get_container_name(deployment, namespace):

    cmd = (
        f"kubectl get deployment {deployment} -n {namespace} "
        f"-o jsonpath='{{.spec.template.spec.containers[0].name}}'"
    )

    name = subprocess.getoutput(cmd).strip()

    return name if name else deployment


#----------------------
# Update the image tag
# ----------------------------
def image_tag(deployment, namespace, imagetag):

    container = get_container_name(deployment, namespace)

    notify(f"[ACTION] Updating image: {deployment} (container: {container}) -> {imagetag}")

    cmd = (
        f"kubectl set image deployment/{deployment} "
        f"{container}={imagetag} -n {namespace}"
    )

    subprocess.run(cmd, shell=True)

    time.sleep(2)



# ----------------------------
# Scale Deployment
# ----------------------------
def scale_deployment(deployment, namespace, replicas=3):

    notify(f"[ACTION] Scaling deployment: {deployment} → {replicas}")

    cmd = (
        f"kubectl scale deployment/{deployment} "
        f"--replicas={replicas} -n {namespace}"
    )

    subprocess.run(cmd, shell=True)

    time.sleep(2)


# ----------------------------
# Increase Memory Limit
# ----------------------------
def bump_memory_limit(deployment, namespace, container, new_limit="512Mi"):

    notify(f"[ACTION] Updating memory limit: {deployment} → {new_limit}")

    cmd = (
        f"kubectl set resources deployment/{deployment} "
        f"-c {container} --limits=memory={new_limit} -n {namespace}"
    )

    subprocess.run(cmd, shell=True)

    time.sleep(2)


# ----------------------------
# Rollback Deployment
# ----------------------------
def rollback_deployment(deployment, namespace):

    notify(f"[ACTION] Rolling back deployment: {deployment}")

    cmd = (
        f"kubectl rollout undo deployment/{deployment} "
        f"-n {namespace}"
    )

    subprocess.run(cmd, shell=True)

    time.sleep(2)


# ----------------------------
# Optional helper (safe debug action)
# ----------------------------
def describe_pod(pod, namespace):

    notify(f"[ACTION] Describing pod: {pod}")

    cmd = (
        f"kubectl describe pod {pod} -n {namespace}"
    )

    output = subprocess.getoutput(cmd)

    return output
