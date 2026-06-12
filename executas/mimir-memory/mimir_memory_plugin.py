"""
Recall — Mimir Memory Executa plugin for Anna.

Persistent memory backend via the Mimir binary (MCP JSON-RPC over stdio).
This plugin spawns mimir as a persistent subprocess, handles the MCP handshake,
and proxies Anna Executa invoke() calls to mimir tools.

Protocol: Executa (described) over stdin/stdout — JSON-RPC 2.0, line-delimited.
Supports: describe, invoke, health.
"""

import hashlib
import json
import os
import queue
import subprocess
import sys
import threading
import time


# ── Configuration ──────────────────────────────────────────────────────────

MIMIR_BIN = os.environ.get("MIMIR_BIN", "mimir")
MIMIR_DB = os.environ.get(
    "MIMIR_DB", os.path.join(os.path.expanduser("~"), ".anna", "recall.db")
)


def _mcp_timeout_s() -> float:
    """Read timeout for a single MCP round-trip (env-overridable per call)."""
    try:
        return float(os.environ.get("RECALL_MCP_TIMEOUT", "30"))
    except ValueError:
        return 30.0


class MemoryUnavailableError(RuntimeError):
    """Raised when the Mimir backend is down and could not be restarted."""


# ── Manifest ───────────────────────────────────────────────────────────────

MANIFEST = {
    "name": "mimir-memory",
    "display_name": "Recall Memory",
    "version": "1.0.0",
    "description": (
        "Persistent, searchable memory for Anna. The agent can remember "
        "facts, preferences, decisions, and context across conversations — "
        "then recall them later by keyword, category, or topic."
    ),
    "author": "Thomas Connally / Nous Research",
    "homepage": "https://github.com/tcconnally/anna-recall",
    "icon": "🧠",
    "category": "memory",
    "license": "MIT",
    "tools": [
        {
            "name": "remember",
            "description": (
                "Store something worth remembering. Use after the user shares "
                "a preference, makes a decision, describes their setup, or gives "
                "any information likely to matter later. "
                "Be specific — a crisp fact is more useful than a vague summary."
            ),
            "parameters": [
                {
                    "name": "fact",
                    "type": "string",
                    "description": "The specific fact or information to store.",
                    "required": True,
                },
                {
                    "name": "category",
                    "type": "string",
                    "description": (
                        "Category: preference, decision, project, person, "
                        "setup, insight, reference, or custom."
                    ),
                    "enum": [
                        "preference",
                        "decision",
                        "project",
                        "person",
                        "setup",
                        "insight",
                        "reference",
                    ],
                    "required": True,
                },
                {
                    "name": "key",
                    "type": "string",
                    "description": (
                        "Short unique key summarizing the fact "
                        "(e.g. 'uses-neovim', 'deploy-target-aws'). "
                        "Auto-generated if omitted."
                    ),
                    "required": False,
                },
                {
                    "name": "tags",
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags for grouping (e.g. ['python', 'devops']).",
                    "required": False,
                },
                {
                    "name": "importance",
                    "type": "number",
                    "description": "How important this is, 0.0–1.0. Default 0.7.",
                    "required": False,
                    "default": 0.7,
                },
            ],
        },
        {
            "name": "recall",
            "description": (
                "Search memory for relevant facts. Call this BEFORE answering "
                "a question where past context would help — the user's name, "
                "preferences, previous decisions, project details, etc. "
                "Returns matches ranked by relevance."
            ),
            "parameters": [
                {
                    "name": "query",
                    "type": "string",
                    "description": "What to search for — keywords, topic, question.",
                    "required": True,
                },
                {
                    "name": "limit",
                    "type": "integer",
                    "description": "Maximum results to return (default 10).",
                    "required": False,
                    "default": 10,
                },
                {
                    "name": "category",
                    "type": "string",
                    "description": "Filter by category (e.g. 'preference').",
                    "required": False,
                },
            ],
        },
        {
            "name": "forget",
            "description": (
                "Soft-delete a memory (recoverable). Use when the user "
                "corrects outdated info or asks you to forget something."
            ),
            "parameters": [
                {
                    "name": "category",
                    "type": "string",
                    "description": "Category of the memory to forget.",
                    "required": True,
                },
                {
                    "name": "key",
                    "type": "string",
                    "description": "Key of the memory to forget.",
                    "required": True,
                },
            ],
        },
        {
            "name": "context",
            "description": (
                "Get a formatted markdown block of the most important/recent "
                "memories for session injection. Call this at the start of "
                "a conversation to load relevant context."
            ),
            "parameters": [
                {
                    "name": "limit",
                    "type": "integer",
                    "description": "Maximum memories to include (default 10).",
                    "required": False,
                    "default": 10,
                }
            ],
        },
        {
            "name": "stats",
            "description": "Get memory database statistics — count, categories, size.",
            "parameters": [],
        },
        {
            "name": "health",
            "description": "Check if the memory system is healthy and reachable.",
            "parameters": [],
        },
    ],
}


# ── Mimir subprocess management ────────────────────────────────────────────

_mimir_proc = None
_mcp_counter = 1
_stdout_queue = None  # queue.Queue fed by the reader thread; None sentinel = EOF


def _drain_stdout(proc, out_queue):
    """Reader thread: forward mimir stdout lines into a queue.

    Decouples reads from the request loop so _mcp_send can enforce a
    deadline (a blocking readline cannot be interrupted portably), and
    guarantees the pipe is always drained. Puts None on EOF so waiters
    learn the process died instead of blocking forever.
    """
    try:
        for line in proc.stdout:
            out_queue.put(line)
    except (OSError, ValueError):
        pass  # pipe closed mid-read — treated the same as EOF
    out_queue.put(None)


def _start_mimir():
    """Spawn mimir as a persistent subprocess and complete the MCP handshake."""
    global _mimir_proc, _mcp_counter, _stdout_queue

    os.makedirs(os.path.dirname(MIMIR_DB) or ".", exist_ok=True)

    _mimir_proc = subprocess.Popen(
        [MIMIR_BIN, "serve", "--db", MIMIR_DB],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        # DEVNULL, never PIPE: an undrained stderr pipe fills up and
        # deadlocks mimir once it blocks on the next stderr write.
        stderr=subprocess.DEVNULL,
        text=True,
    )
    _mcp_counter = 1
    _stdout_queue = queue.Queue()
    threading.Thread(
        target=_drain_stdout, args=(_mimir_proc, _stdout_queue), daemon=True
    ).start()

    # MCP initialize handshake. No restart-on-failure here: if the process
    # we just spawned can't complete the handshake, restarting would loop.
    _mcp_send(
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "anna-recall", "version": "1.0.0"},
        },
        allow_restart=False,
    )

    # Send 'initialized' notification (no id, no response expected)
    _mimir_proc.stdin.write(
        json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"
    )
    _mimir_proc.stdin.flush()


def _mimir_alive():
    return _mimir_proc is not None and _mimir_proc.poll() is None


def _ensure_mimir(allow_restart=True):
    """Make sure mimir is running, attempting one restart if it died."""
    if _mimir_alive():
        return
    if not allow_restart:
        raise MemoryUnavailableError(
            "Memory backend unavailable — mimir is not running"
        )
    try:
        _start_mimir()
    except MemoryUnavailableError:
        raise
    except Exception as e:
        raise MemoryUnavailableError(
            f"Memory backend unavailable — mimir restart failed: {e}"
        ) from e


def _mcp_send(method, params=None, allow_restart=True):
    """Send an MCP request to mimir and return the result.

    Restarts mimir once if it died since the last call; raises
    MemoryUnavailableError (never hangs) if the backend stays down or a
    response doesn't arrive within the configured timeout.
    """
    global _mcp_counter
    _ensure_mimir(allow_restart=allow_restart)

    req_id = _mcp_counter
    _mcp_counter += 1

    req = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params:
        req["params"] = params

    try:
        _mimir_proc.stdin.write(json.dumps(req) + "\n")
        _mimir_proc.stdin.flush()
    except (BrokenPipeError, OSError) as e:
        raise MemoryUnavailableError(
            f"Memory backend unavailable — mimir pipe closed: {e}"
        ) from e

    # Read responses until we find the one matching our request id.
    # MCP servers may send notifications (no id) between responses.
    deadline = time.monotonic() + _mcp_timeout_s()
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise MemoryUnavailableError(
                f"Memory backend unavailable — mimir did not respond to "
                f"'{method}' within {_mcp_timeout_s():.0f}s"
            )
        try:
            line = _stdout_queue.get(timeout=remaining)
        except queue.Empty:
            continue  # loop re-checks the deadline
        if line is None:
            raise MemoryUnavailableError(
                "Memory backend unavailable — mimir process exited unexpectedly"
            )
        try:
            resp = json.loads(line.strip())
        except json.JSONDecodeError:
            continue
        if resp.get("id") == req_id:
            if "result" in resp:
                return resp["result"]
            if "error" in resp:
                msg = resp["error"].get("message", str(resp["error"]))
                raise RuntimeError(f"mimir error: {msg}")
            raise RuntimeError(f"unexpected mimir response: {resp}")
        # Notifications or other responses — skip


# ── Tool mapping ───────────────────────────────────────────────────────────

# Map Anna Executa tool names → mimir MCP tool names + argument transforms
TOOL_MAP = {
    "remember": {
        "mcp_tool": "mimir_remember",
        "transform": lambda args: {
            "category": args.get("category", "insight"),
            "key": args.get("key") or _make_key(args.get("fact", "")),
            "body_json": json.dumps({"fact": args.get("fact", "")}),
            "tags": args.get("tags", []),
            "importance": args.get("importance", 0.7),
            "type": "insight",
            "status": "active",
        },
    },
    "recall": {
        "mcp_tool": "mimir_recall",
        "transform": lambda args: {
            "query": args.get("query", ""),
            "limit": args.get("limit", 10),
            "category": args.get("category"),
        },
    },
    "forget": {
        "mcp_tool": "mimir_forget",
        "transform": lambda args: {
            "category": args.get("category", ""),
            "key": args.get("key", ""),
        },
    },
    "context": {
        "mcp_tool": "mimir_context",
        "transform": lambda args: {
            "limit": args.get("limit", 10),
        },
    },
    "stats": {
        "mcp_tool": "mimir_stats",
        "transform": lambda args: {},
    },
    "health": {
        "mcp_tool": "mimir_health",
        "transform": lambda args: {},
    },
}


def _make_key(fact: str, max_len: int = 50) -> str:
    """Generate a key from a fact string.

    Ends with a short content hash so two distinct facts that share a
    prefix don't collide on the same key — mimir treats (category, key)
    as identity and an unsuffixed collision silently overwrites the
    earlier fact.
    """
    import re

    digest = hashlib.sha256(fact.encode("utf-8")).hexdigest()[:8]
    key = fact.lower().strip()
    key = re.sub(r"[^a-z0-9\s-]", "", key)
    key = re.sub(r"\s+", "-", key)
    if len(key) > max_len:
        key = key[:max_len].rsplit("-", 1)[0]
    key = key.strip("-") or "untitled"
    return f"{key}-{digest}"


# ── Request handler ────────────────────────────────────────────────────────


def handle(req: dict) -> dict:
    """Handle a single JSON-RPC request from Anna."""
    req_id = req.get("id")
    method = req.get("method")

    # describe — return the manifest once at startup
    if method == "describe":
        return {"jsonrpc": "2.0", "id": req_id, "result": MANIFEST}

    # health — check mimir reachable via its health tool
    if method == "health":
        try:
            _mcp_send("tools/call", {"name": "mimir_health", "arguments": {}})
            return {"jsonrpc": "2.0", "id": req_id, "result": {"status": "healthy"}}
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"status": "degraded", "detail": str(e)},
            }

    # invoke — execute a tool
    if method == "invoke":
        params = req.get("params") or {}
        tool_name = params.get("tool", "")
        args = params.get("arguments") or {}

        if tool_name not in TOOL_MAP:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
            }

        mapping = TOOL_MAP[tool_name]
        try:
            mcp_args = mapping["transform"](args)
            result = _mcp_send("tools/call", {
                "name": mapping["mcp_tool"],
                "arguments": mcp_args,
            })

            # Extract the actual content from MCP response
            content = result.get("content", [])
            text_parts = []
            for item in content:
                if item.get("type") == "text":
                    text_parts.append(item["text"])

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "success": True,
                    "data": {
                        "output": "\n".join(text_parts) if text_parts else json.dumps(result),
                        "raw": result,
                    },
                },
            }

        except MemoryUnavailableError as e:
            # Backend down and restart failed — tell the agent plainly so it
            # can answer without memory instead of presenting a stack trace.
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": str(e)},
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": str(e)},
            }

    # Unknown method
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"},
    }


# ── Main loop ──────────────────────────────────────────────────────────────


def main():
    # Start mimir first so describe responds quickly
    try:
        _start_mimir()
    except Exception as e:
        # If mimir fails to start, we can still serve describe but
        # invoke calls will fail gracefully with clear errors.
        print(f"[recall] WARNING: mimir startup failed: {e}", file=sys.stderr)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        try:
            resp = handle(req)
        except Exception as e:
            resp = {
                "jsonrpc": "2.0",
                "id": req.get("id"),
                "error": {"code": -32603, "message": str(e)},
            }

        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()

    # Clean shutdown
    if _mimir_proc and _mimir_proc.poll() is None:
        try:
            _mimir_proc.stdin.close()
            _mimir_proc.wait(timeout=5)
        except (subprocess.TimeoutExpired, OSError):
            _mimir_proc.kill()


if __name__ == "__main__":
    main()
