# Task 2 Plan: The Documentation Agent

## Tools
- `read_file(path)` — reads file contents, blocks `../` traversal
- `list_files(path)` — lists directory entries, blocks `../` traversal

## Tool schemas
Register both tools as OpenAI function-calling schemas in the LLM request.

## Agentic loop
1. Send question + tool definitions to LLM
2. If LLM returns tool_calls → execute each tool, append result as `tool` role message, repeat
3. If LLM returns text → output final JSON and exit
4. Stop after 10 tool calls max

## System prompt strategy
Tell LLM to use `list_files` to discover wiki files, then `read_file` to find the answer, and include source as `file#section`.

## Output
JSON with `answer`, `source`, `tool_calls` fields.
