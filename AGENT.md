# Agent Documentation

## Overview
A CLI agent that takes a question, uses tools to read the project wiki, and returns a structured JSON answer.

## LLM Provider
- Provider: Qwen Code API (deployed on VM)
- Model: qwen3-coder-plus
- API: OpenAI-compatible chat completions

## Tools
- `list_files(path)` — lists files in a directory (blocks `../` traversal)
- `read_file(path)` — reads file contents (blocks `../` traversal)

## Agentic loop
1. Send question + tool definitions to LLM
2. If LLM returns tool_calls → execute each tool, append result, repeat
3. If LLM returns text → output final JSON and exit
4. Stop after 10 tool calls max

## System prompt strategy
The agent is instructed to always use `list_files` to discover wiki files, then `read_file` to find the answer, and include source as `wiki/filename.md#section`.

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
{"answer": "...", "source": "wiki/file.md#section", "tool_calls": [...]}
```

## Run tests
```bash
uv run pytest tests/ -v
```
