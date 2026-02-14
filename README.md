# Incident Resolution AI Agent (Agentic AI for DevOps)

This project demonstrates a real-world **Agentic AI system** that automatically
detects, analyzes, and resolves Kubernetes incidents using an LLM.

## Features
- Reads pod status and logs
- Uses LLM for decision making
- Executes real DevOps actions
- Includes feedback loop
- Human escalation support

## Architecture
Observe → Reason → Decide → Act → Learn

## Prerequisites
- Kubernetes cluster
- kubectl configured
- Python 3.9+
- OpenAI API key

## Setup

```bash
pip install -r requirements.txt
export OPENAI_API_KEY="your_api_key"
