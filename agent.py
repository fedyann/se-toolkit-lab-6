import sys
import json
import os
import re
import requests
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(".env.agent.secret")
load_dotenv(".env.docker.secret")

PROJECT_ROOT = Path(__file__).parent.resolve()

def read_file(path: str) -> str:
    target = (PROJECT_ROOT / path).resolve()
    if not str(target).startswith(str(PROJECT_ROOT)):
        return "Error: access outside project directory is not allowed."
    if not target.exists():
        return f"Error: file '{path}' does not exist."
    return target.read_text(encoding="utf-8")

def list_files(path: str) -> str:
    target = (PROJECT_ROOT / path).resolve()
    if not str(target).startswith(str(PROJECT_ROOT)):
        return "Error: access outside project directory is not allowed."
    if not target.exists():
        return f"Error: directory '{path}' does not exist."
    entries = [e.name for e in target.iterdir()]
    return "\n".join(entries)

def query_api(method: str, path: str, body: str = None, no_auth: bool = False) -> str:
    api_key = os.getenv("LMS_API_KEY")
    base_url = os.getenv("AGENT_API_BASE_URL", "http://localhost:42002")
    url = base_url.rstrip("/") + "/" + path.lstrip("/")
    headers = {"Content-Type": "application/json"}
    if not no_auth:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        if method.upper() == "GET":
            resp = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == "POST":
            resp = requests.post(url, headers=headers, data=body, timeout=10)
        else:
            resp = requests.request(method.upper(), url, headers=headers, data=body, timeout=10)
        return json.dumps({"status_code": resp.status_code, "body": resp.text[:500]})
    except Exception as e:
        return json.dumps({"status_code": 0, "body": str(e)})

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the project repository. Use for source code, configs, and documentation files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from project root."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories at a given path in the project repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative directory path from project root."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_api",
            "description": "Call the deployed backend API to get live data. Use for questions about item counts, scores, analytics, or any data stored in the database. Also use to test authentication by setting no_auth=true.",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {"type": "string", "description": "HTTP method: GET, POST, etc."},
                    "path": {"type": "string", "description": "API path, e.g. /items/ or /analytics/scores?lab=lab-04"},
                    "body": {"type": "string", "description": "Optional JSON request body for POST requests."},
                    "no_auth": {"type": "boolean", "description": "Set to true to make request without authentication header, to test what status code unauthenticated requests get."}
                },
                "required": ["method", "path"]
            }
        }
    }
]

def execute_tool(name: str, args: dict) -> str:
    if name == "read_file":
        return read_file(args["path"])
    elif name == "list_files":
        return list_files(args["path"])
    elif name == "query_api":
        return query_api(args["method"], args["path"], args.get("body"), args.get("no_auth", False))
    return f"Error: unknown tool '{name}'."

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run agent.py \"Your question\"", file=sys.stderr)
        sys.exit(1)

    question = sys.argv[1]

    api_key = os.getenv("LLM_API_KEY")
    api_base = os.getenv("LLM_API_BASE")
    model = os.getenv("LLM_MODEL", "qwen3-coder-plus")

    client = OpenAI(api_key=api_key, base_url=api_base)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a system agent for a software engineering course project. "
                "Project structure: "
                "- wiki/ — documentation markdown files. "
                "- backend/app/ — Python backend source code. "
                "- backend/app/routers/ — API routers: analytics.py, interactions.py, items.py, learners.py, pipeline.py. "
                "- backend/app/models/ — database models. "
                "- frontend/ — frontend source code. "
                "- pyproject.toml — project dependencies. "
                "You have three tools: "
                "1. list_files — discover files in the project. "
                "2. read_file — read wiki docs, source code, config files. "
                "3. query_api — call the live backend API for data questions. "
                "Rules: "
                "- For wiki/documentation questions: use list_files then read_file on wiki/. "
                "- For framework, routers, project structure questions: read source code in backend/app/. "
                "- For counts, scores, items, analytics, live data: use query_api. "
                "- For authentication/status code questions: use query_api with no_auth=true. "
                "- IMPORTANT: Do NOT give partial or intermediate answers like 'Let me check...'. "
                "- IMPORTANT: Only respond with text when you have ALL the information needed for a complete answer. "
                "- IMPORTANT: If you need to read multiple files, read ALL of them before giving your final answer. "
                "- Include source as 'wiki/filename.md#section' when answering from docs. "
                "- Be concise and precise."
            )
        },
        {"role": "user", "content": question}
    ]

    tool_calls_log = []
    max_tool_calls = 15
    tool_call_count = 0
    answer = ""
    source = ""

    while tool_call_count < max_tool_calls:
        print(f"Calling LLM (iteration {tool_call_count + 1})...", file=sys.stderr)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            timeout=60
        )

        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            for tc in msg.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments)
                print(f"Tool call: {name}({args})", file=sys.stderr)
                result = execute_tool(name, args)
                tool_calls_log.append({"tool": name, "args": args, "result": result})
                tool_call_count += 1
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result
                })
        else:
            answer = (msg.content or "").strip()
            incomplete_phrases = ["let me", "let me check", "let me look", "i'll check", "i need to"]
            if any(answer.lower().startswith(p) for p in incomplete_phrases) and tool_call_count < max_tool_calls:
                messages.append({"role": "assistant", "content": answer})
                messages.append({"role": "user", "content": "Continue and provide your complete final answer now."})
                continue
            # Extract source - wiki/ or backend/ references
            matches = re.findall(r'(?:wiki|backend)/[\w\-/]+\.(?:md|py)(?:#[\w\-]+)?', answer)
            if matches:
                source = matches[0]
            else:
                for tc in tool_calls_log:
                    if tc["tool"] == "read_file":
                        path = tc["args"].get("path", "")
                        if "wiki/" in path or "backend/" in path:
                            source = path
                            break
            break

    result = {"answer": answer, "source": source, "tool_calls": tool_calls_log}
    print(json.dumps(result))

if __name__ == "__main__":
    main()
