import subprocess
import json

def test_framework_question_uses_read_file():
    result = subprocess.run(
        ["uv", "run", "agent.py", "What Python web framework does this project's backend use?"],
        capture_output=True,
        text=True,
        timeout=120
    )
    assert result.returncode == 0
    output = json.loads(result.stdout.strip())
    assert "answer" in output
    assert "tool_calls" in output
    tool_names = [tc["tool"] for tc in output["tool_calls"]]
    assert "read_file" in tool_names

def test_items_count_uses_query_api():
    result = subprocess.run(
        ["uv", "run", "agent.py", "How many items are currently stored in the database?"],
        capture_output=True,
        text=True,
        timeout=120
    )
    assert result.returncode == 0
    output = json.loads(result.stdout.strip())
    assert "answer" in output
    assert "tool_calls" in output
    tool_names = [tc["tool"] for tc in output["tool_calls"]]
    assert "query_api" in tool_names
