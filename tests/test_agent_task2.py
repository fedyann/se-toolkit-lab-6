import subprocess
import json

def test_merge_conflict_uses_read_file():
    result = subprocess.run(
        ["uv", "run", "agent.py", "How do you resolve a merge conflict?"],
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
    sources = [tc["args"].get("path", "") for tc in output["tool_calls"] if tc["tool"] == "read_file"]
    assert any("wiki/" in s for s in sources)

def test_list_wiki_files_uses_list_files():
    result = subprocess.run(
        ["uv", "run", "agent.py", "What files are in the wiki?"],
        capture_output=True,
        text=True,
        timeout=120
    )
    assert result.returncode == 0
    output = json.loads(result.stdout.strip())
    assert "answer" in output
    assert "tool_calls" in output
    tool_names = [tc["tool"] for tc in output["tool_calls"]]
    assert "list_files" in tool_names
