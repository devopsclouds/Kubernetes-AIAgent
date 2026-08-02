FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && \
    curl -LO "https://dl.k8s.io/release/$(curl -L -s \
    https://dl.k8s.io/release/stable.txt)/bin/linux/arm64/kubectl" && \
    chmod +x kubectl && mv kubectl /usr/local/bin/ && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install flask
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY webhook_listener.py .
COPY observer_multi.py .
COPY agent_multi.py .
COPY actions_multi.py .
COPY llm_brain.py .
#COPY ollama_brain.py .
COPY notifications.py .
#COPY metrics.py .
COPY config.py .
COPY prompts/ prompts/

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5005", \
     "--timeout", "120", "--log-level", "info", \
     "webhook_listener:app"]
