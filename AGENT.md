# Agent Documentation

## Overview
A CLI agent that takes a question, uses tools to read the project wiki, source code, and query the live backend API, then returns a structured JSON answer.

## LLM Provider
- Provider: Qwen Code API (deployed on VM)
- Model: qwen3-coder-plus
- API: OpenAI-compatible chat completions

## Tools

### list_files(path)
Lists files in a directory. Blocks `../` path traversal for security.

### read_file(path)
Reads file contents from the project. Used for wiki docs, source code, and config files. Blocks `../` path traversal for security.

### query_api(method, path, body, no_auth)
Calls the deployed backend API. Used for live data questions (item counts, scores, analytics).
- Authenticates with `LMS_API_KEY` from environment variables
- Base URL from `AGENT_API_BASE_URL` (defaults to `http://localhost:42002`)
- `no_auth=true` skips authentication header (for testing unauthenticated requests)

## Environment Variables
| Variable | Purpose |
|---|---|
| `LLM_API_KEY` | LLM provider API key |
| `LLM_API_BASE` | LLM API endpoint URL |
| `LLM_MODEL` | Model name |
| `LMS_API_KEY` | Backend API key for query_api |
| `AGENT_API_BASE_URL` | Backend base URL (default: http://localhost:42002) |

## Agentic Loop
1. Send question + tool definitions to LLM
2. If LLM returns tool_calls → execute each tool, append result, repeat
3. If LLM returns incomplete answer → prompt for complete answer
4. If LLM returns complete text → output final JSON and exit
5. Stop after 15 tool calls max

## System Prompt Strategy
The agent decides which tool to use based on question type:
- Wiki/documentation questions → list_files + read_file on wiki/
- Framework/code/routers questions → read_file on backend/app/
- Live data questions → query_api
- Auth/status code questions → query_api with no_auth=true

## How to Run

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

## Output Format
```json
{"answer": "...", "source": "wiki/file.md#section", "tool_calls": [...]}
```

## Benchmark Results
- Local eval: 10/10 passed
- Key lessons learned:
  - LLM needs explicit instructions to not give partial answers
  - Source extraction needs to cover both wiki/ and backend/ paths
  - no_auth parameter essential for testing unauthenticated API requests
  - Increasing max_tool_calls to 15 helps for multi-file questions

## Run Tests
```bash
uv run pytest tests/ -v
```
