# Task 1 Plan: Call an LLM from Code

## LLM Provider
- Provider: Qwen Code API (deployed on VM)
- Model: qwen3-coder-plus
- Base URL: http://<vm-ip>:42005/v1

## Structure
1. Parse CLI argument (question)
2. Load env vars from .env.agent.secret
3. Send request to LLM API (OpenAI-compatible)
4. Parse response and output JSON to stdout
