# config.py

NAMESPACE = "dev"
POD_NAME = "payment-service-764f584496-lbvg2"
DEPLOYMENT_NAME = "payment-service"
APP_LABEL = "app=payment-service"

ALLOWED_ACTIONS = [
    "RESTART_POD",
    "SCALE_DEPLOYMENT",
    "DO_NOTHING",
    "ESCALATE_TO_HUMAN"
]

WAIT_TIME = 60