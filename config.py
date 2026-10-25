# config.py
#import subprocess
NAMESPACE = "dev"
#Memory limit to apply when a pod is OOMKilled.
OOM_MEMORY_LIMIT = "700Mi"
KNOWN_GOOD_IMAGES = {
    "login-service": "nginx",
    "cart-service": "busybox",
    "payment-service": "busybox",
}

ALLOWED_ACTIONS = [
    "RESTART_POD",
    "SCALE_DEPLOYMENT",
    "IMAGE_TAG",
    "DO_NOTHING",
    "ESCALATE_TO_HUMAN"
]

PENDING_MEMORY_REQUEST = "128Mi"
PENDING_MEMORY_LIMIT = "256Mi"
PENDING_CPU_REQUEST = "100m"
PENDING_CPU_LIMIT = "500m"

WAIT_TIME = 60
