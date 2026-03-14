# Task 3 Plan: The System Agent

## New tool: query_api
- Parameters: method, path, body (optional)
- Returns: JSON with status_code and body
- Auth: LMS_API_KEY from environment variables
- Base URL: AGENT_API_BASE_URL (default: http://localhost:42002)

## Environment variables
- LLM_API_KEY, LLM_API_BASE, LLM_MODEL — LLM config
- LMS_API_KEY — backend auth
- AGENT_API_BASE_URL — backend base URL

## System prompt updates
- Use list_files/read_file for wiki and source code questions
- Use query_api for data-dependent questions (item count, scores)
- Use read_file on backend source code for framework/config questions

## Steps
1. Add query_api tool schema
2. Implement query_api function
3. Update system prompt
4. Run run_eval.py and iterate
