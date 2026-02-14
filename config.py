# config.py

NAMESPACE = "dev"
POD_NAME = "payment-service-7599dc754c-hghk7"
DEPLOYMENT_NAME = "payment-service"
APP_LABEL = "app=payment-service"

ALLOWED_ACTIONS = [
    "RESTART_POD",
    "SCALE_DEPLOYMENT",
    "DO_NOTHING",
    "ESCALATE_TO_HUMAN"
]

WAIT_TIME = 60
