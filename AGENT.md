# Agent Documentation

## Overview
A CLI agent that takes a question as input, sends it to an LLM, and returns a structured JSON answer.

## LLM Provider
- Provider: Qwen Code API (deployed on VM)
- Model: qwen3-coder-plus
- API: OpenAI-compatible chat completions

## How to run

1. Fill in `.env.agent.secret`:
```
   LLM_API_KEY=your-key
   LLM_API_BASE=http://<vm-ip>:42005/v1
   LLM_MODEL=qwen3-coder-plus
```

2. Run the agent:
```bash
   uv run agent.py "Your question here"
```

## Output format
```json
{"answer": "...", "tool_calls": []}
```

## Run tests
```bash
uv run pytest tests/test_agent.py -v
```
