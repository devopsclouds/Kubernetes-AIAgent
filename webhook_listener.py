import json
import threading
import subprocess
import os

from flask import Flask, request, jsonify
from observer_multi import collect_context
from agent_multi import decide_action, execute_action
from notifications import notify, send_email
from config import NAMESPACE

app = Flask(__name__)


def extract_pod_info(alert):
    """Extract pod name and namespace from Alertmanager alert labels."""
    labels = alert.get("labels", {})
    pod = labels.get("pod")
    namespace = labels.get("namespace", NAMESPACE)
    status = alert.get("status", "firing")
    alert_name = labels.get("alertname", "Unknown")
    return pod, namespace, status, alert_name


def run_agent_for_pod(pod, namespace, alert_name):
    """
    Run the full agent loop for a specific pod triggered by Prometheus alert.
    This is the same logic as agent_multi.py but targeted at one pod.
    """
    try:
        notify(f"[WEBHOOK] Alert received: {alert_name} for pod {pod}")

        # Step 1: Collect context (same as observer_multi.py)
        context = collect_context(pod, namespace)

        notify(f"[WEBHOOK] Pod status: {context['status']}")

        # Step 2: Skip if already healthy
        if context["status"] in ("Running", "RunningWithPriorRestarts"):
            notify(f"[WEBHOOK] {pod} looks healthy now - no action needed")
            return

        # Step 3: Decide action (same as agent_multi.py)
        action = decide_action(context)

        notify(f"[WEBHOOK] Decided action: {action} for {pod}")

        # Step 4: Execute action (same as agent_multi.py)
        execute_action(action, context)

        # Step 5: Send success email
        send_email(
            subject=f"[K8s Agent] Auto-fixed: {pod}",
            body=(
                f"Alert: {alert_name}\n"
                f"Pod: {pod}\n"
                f"Namespace: {namespace}\n"
                f"Status detected: {context['status']}\n"
                f"Action taken: {action}\n\n"
                f"The agent automatically handled this incident."
            )
        )

    except Exception as e:
        notify(f"[WEBHOOK] Agent failed for {pod}: {e}", alert=True)


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Receives Alertmanager webhook POST.
    Alertmanager sends a JSON body with 'alerts' list.
    Each alert has 'labels' containing pod, namespace, alertname.
    """
    data = request.get_json(silent=True) or {}
    alerts = data.get("alerts", [])

    for alert in alerts:
        pod, namespace, status, alert_name = extract_pod_info(alert)

        if not pod:
            notify(f"[WEBHOOK] Alert received but no pod label found - skipping")
            continue

        # Only act on firing alerts, not resolved ones
        if status == "resolved":
            notify(f"[WEBHOOK] {pod} resolved - no action needed")
            continue

        # Run agent in background thread so webhook returns immediately
        # Alertmanager expects a fast response (within seconds)
        threading.Thread(
            target=run_agent_for_pod,
            args=(pod, namespace, alert_name)
        ).start()

    return jsonify({
        "status": "received",
        "alerts_count": len(alerts)
    }), 200


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200


@app.route("/test", methods=["GET"])
def test():
    """
    Test endpoint - trigger agent manually for a specific pod.
    Usage: curl http://localhost:5005/test?pod=login-service-xxx&namespace=dev
    """
    pod = request.args.get("pod")
    namespace = request.args.get("namespace", NAMESPACE)

    if not pod:
        return jsonify({"error": "pod parameter required"}), 400

    threading.Thread(
        target=run_agent_for_pod,
        args=(pod, namespace, "ManualTest")
    ).start()

    return jsonify({
        "status": "triggered",
        "pod": pod,
        "namespace": namespace
    }), 200


if __name__ == "__main__":
    notify("Webhook listener started on port 5005")
    notify("Waiting for Alertmanager alerts...")
    notify("Email handled by Alertmanager directly")
    app.run(host="0.0.0.0", port=5005, debug=False)

# Gunicorn entry point (used when running inside Kubernetes)
# Start with: gunicorn -w 2 -b 0.0.0.0:5005 webhook_listener:app
