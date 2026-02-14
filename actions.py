
import subprocess

def restart_pod(deployment, namespace):
    subprocess.run(
        f"kubectl rollout restart  deploy {deployment} -n {namespace}",
        shell=True
    )

def scale_deployment(deployment, namespace, replicas=3):
    subprocess.run(
        f"kubectl scale deployment {deployment} -n {namespace} --replicas={replicas}",
        shell=True
    )

def notify(message):
    print(f"[NOTIFICATION]: {message}")
