"""Unit tests for the Recall (mimir-memory) Executa plugin.

These run without a real mimir binary: backend calls are stubbed at the
_mcp_send seam, and the subprocess machinery is tested against fake
process objects.
"""

import io
import os
import queue
import sys
import threading

import pytest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "executas", "mimir-memory"),
)

import mimir_memory_plugin as plugin  # noqa: E402


# ── handle(): protocol behavior ─────────────────────────────────────────────


def test_describe_returns_manifest():
    resp = plugin.handle({"id": 1, "method": "describe"})
    assert resp["result"]["name"] == "mimir-memory"
    tool_names = {t["name"] for t in resp["result"]["tools"]}
    assert {"remember", "recall", "forget", "context", "stats", "health"} <= tool_names


def test_invoke_remember_maps_to_mimir_tool(monkeypatch):
    calls = []

    def fake_send(method, params=None, allow_restart=True):
        calls.append((method, params))
        return {"content": [{"type": "text", "text": "stored"}]}

    monkeypatch.setattr(plugin, "_mcp_send", fake_send)

    resp = plugin.handle(
        {
            "id": 2,
            "method": "invoke",
            "params": {
                "tool": "remember",
                "arguments": {"fact": "user prefers tabs", "category": "preference"},
            },
        }
    )

    assert resp["result"]["success"] is True
    assert resp["result"]["data"]["output"] == "stored"
    method, params = calls[0]
    assert method == "tools/call"
    assert params["name"] == "mimir_remember"
    assert params["arguments"]["category"] == "preference"
    assert params["arguments"]["key"]  # auto-generated


def test_invoke_unknown_tool_returns_method_not_found():
    resp = plugin.handle(
        {"id": 3, "method": "invoke", "params": {"tool": "nope", "arguments": {}}}
    )
    assert resp["error"]["code"] == -32601


def test_unknown_method_returns_error():
    resp = plugin.handle({"id": 4, "method": "bogus"})
    assert resp["error"]["code"] == -32601


def test_invoke_backend_down_returns_clean_error(monkeypatch):
    def fake_send(method, params=None, allow_restart=True):
        raise plugin.MemoryUnavailableError(
            "Memory backend unavailable — mimir restart failed: boom"
        )

    monkeypatch.setattr(plugin, "_mcp_send", fake_send)

    resp = plugin.handle(
        {
            "id": 5,
            "method": "invoke",
            "params": {"tool": "recall", "arguments": {"query": "x"}},
        }
    )
    assert resp["error"]["code"] == -32603
    assert "Memory backend unavailable" in resp["error"]["message"]
    # The internal exception type must not leak (no AttributeError, no traceback)
    assert "AttributeError" not in resp["error"]["message"]


def test_health_degraded_when_backend_down(monkeypatch):
    def fake_send(method, params=None, allow_restart=True):
        raise plugin.MemoryUnavailableError("Memory backend unavailable")

    monkeypatch.setattr(plugin, "_mcp_send", fake_send)
    resp = plugin.handle({"id": 6, "method": "health"})
    assert resp["result"]["status"] == "degraded"


# ── _make_key(): collision resistance ───────────────────────────────────────


def test_make_key_distinct_facts_with_shared_prefix_do_not_collide():
    a = plugin._make_key("user prefers dark mode in the editor always on")
    b = plugin._make_key("user prefers dark mode in the editor always off")
    assert a != b


def test_make_key_is_deterministic():
    assert plugin._make_key("same fact") == plugin._make_key("same fact")


def test_make_key_handles_symbol_only_input():
    key = plugin._make_key("!!! ???")
    assert key.startswith("untitled-")


# ── _mcp_send(): timeout and restart machinery ──────────────────────────────


class FakeProc:
    """Minimal Popen stand-in: alive until told otherwise, writable stdin."""

    def __init__(self):
        self.stdin = io.StringIO()
        self._alive = True

    def poll(self):
        return None if self._alive else 0


def test_mcp_send_times_out_instead_of_hanging(monkeypatch):
    monkeypatch.setenv("RECALL_MCP_TIMEOUT", "0.2")
    monkeypatch.setattr(plugin, "_mimir_proc", FakeProc())
    monkeypatch.setattr(plugin, "_stdout_queue", queue.Queue())  # never answered

    with pytest.raises(plugin.MemoryUnavailableError, match="did not respond"):
        plugin._mcp_send("tools/call", {"name": "mimir_health", "arguments": {}})


def test_mcp_send_detects_process_exit(monkeypatch):
    monkeypatch.setenv("RECALL_MCP_TIMEOUT", "5")
    q = queue.Queue()
    q.put(None)  # reader thread's EOF sentinel
    monkeypatch.setattr(plugin, "_mimir_proc", FakeProc())
    monkeypatch.setattr(plugin, "_stdout_queue", q)

    with pytest.raises(plugin.MemoryUnavailableError, match="exited unexpectedly"):
        plugin._mcp_send("tools/call", {"name": "mimir_health", "arguments": {}})


def test_mcp_send_skips_notifications_and_matches_id(monkeypatch):
    monkeypatch.setenv("RECALL_MCP_TIMEOUT", "5")
    monkeypatch.setattr(plugin, "_mcp_counter", 7)
    q = queue.Queue()
    q.put('{"jsonrpc":"2.0","method":"notifications/progress"}\n')  # no id — skip
    q.put("not json\n")  # malformed — skip
    q.put('{"jsonrpc":"2.0","id":7,"result":{"ok":true}}\n')
    monkeypatch.setattr(plugin, "_mimir_proc", FakeProc())
    monkeypatch.setattr(plugin, "_stdout_queue", q)

    result = plugin._mcp_send("tools/call", {"name": "mimir_health", "arguments": {}})
    assert result == {"ok": True}


def test_ensure_mimir_raises_clean_error_when_restart_fails(monkeypatch):
    monkeypatch.setattr(plugin, "_mimir_proc", None)

    def failing_start():
        raise FileNotFoundError("mimir binary not found")

    monkeypatch.setattr(plugin, "_start_mimir", failing_start)

    with pytest.raises(plugin.MemoryUnavailableError, match="restart failed"):
        plugin._ensure_mimir()


def test_ensure_mimir_restarts_dead_process(monkeypatch):
    dead = FakeProc()
    dead._alive = False
    monkeypatch.setattr(plugin, "_mimir_proc", dead)

    started = []
    monkeypatch.setattr(plugin, "_start_mimir", lambda: started.append(True))

    plugin._ensure_mimir()
    assert started == [True]


# ── reader thread ───────────────────────────────────────────────────────────


def test_drain_stdout_forwards_lines_and_signals_eof():
    class P:
        stdout = io.StringIO("line one\nline two\n")

    q = queue.Queue()
    t = threading.Thread(target=plugin._drain_stdout, args=(P(), q))
    t.start()
    t.join(timeout=5)

    assert q.get(timeout=1) == "line one\n"
    assert q.get(timeout=1) == "line two\n"
    assert q.get(timeout=1) is None  # EOF sentinel
