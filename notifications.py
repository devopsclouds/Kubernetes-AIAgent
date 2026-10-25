import os
import smtplib
from email.mime.text import MIMEText

EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT", "devops.clouds8978@gmail.com")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def send_email(subject, body):

    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print("[NOTIFY] EMAIL_SENDER/EMAIL_PASSWORD not set - email skipped")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECIPIENT

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, [EMAIL_RECIPIENT], msg.as_string())
        print(f"[NOTIFY] Email sent: {subject}")
    except Exception as e:
        print(f"[NOTIFY] Email send failed: {e}")


def notify(msg, alert=False):
    """
    Always prints to console.
    If alert=True, also emails EMAIL_RECIPIENT.
    """
    print(msg)

    if alert:
        send_email(
            subject="[K8s Incident Agent] Alert",
            body=msg
        )
