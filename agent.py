import sys
import json
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(".env.agent.secret")

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

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the project repository.",
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
            "description": "List files and directories at a given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative directory path from project root."}
                },
                "required": ["path"]
            }
        }
    }
]

def execute_tool(name: str, args: dict) -> str:
    if name == "read_file":
        return read_file(args["path"])
    elif name == "list_files":
        return list_files(args["path"])
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
                "You are a documentation assistant for a software engineering course. "
                "The project has a wiki directory with markdown files. "
                "ALWAYS follow these steps: "
                "1. Use list_files with path='wiki' to see available files. "
                "2. Use read_file to read the most relevant file(s). "
                "3. Only after reading file contents, give your final answer. "
                "NEVER answer without first calling read_file to read the relevant file. "
                "Always include source as 'wiki/filename.md#section-anchor' in your answer text."
            )
        },
        {"role": "user", "content": question}
    ]

    tool_calls_log = []
    max_tool_calls = 10
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
            answer = msg.content.strip()
            for line in answer.split("\n"):
                if "wiki/" in line and "#" in line:
                    for word in line.split():
                        if "wiki/" in word and "#" in word:
                            source = word.strip(".,;:`\"'")
                            break
            break

    result = {"answer": answer, "source": source, "tool_calls": tool_calls_log}
    print(json.dumps(result))

if __name__ == "__main__":
    main()
