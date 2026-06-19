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

# When bundled with PyInstaller, mimir lives alongside the executable.
# sys._MEIPASS is the temp directory where PyInstaller extracts bundled files.
def _find_mimir():
    """Locate the mimir binary: bundled copy first, then env var, then PATH."""
    # 1) Bundled with PyInstaller
    try:
        _base = sys._MEIPASS  # set at runtime by PyInstaller
        bundled = os.path.join(_base, "mimir")
        if os.path.isfile(bundled) and os.access(bundled, os.X_OK):
            return bundled
    except AttributeError:
        pass  # not running under PyInstaller

    # 2) Explicit env var
    env_bin = os.environ.get("MIMIR_BIN")
    if env_bin:
        return env_bin

    # 3) Fall back to PATH
    return "mimir"


MIMIR_BIN = _find_mimir()
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
    "version": "1.0.2",
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
                "Store a fact in persistent memory so it survives across conversations. "
                "CALL THIS when the user explicitly shares something important: "
                "a preference ('I prefer tabs'), a tool choice ('we use pytest'), "
                "a deployment detail ('deployed to Fly.io'), a name, a project name, "
                "or a decision they made. "
                "ALSO CALL when you learn something the hard way that will save time later "
                "(a bug fix, a config trick, a gotcha). "
                "DO NOT call for small talk, transient queries, or anything the user "
                "would not expect you to remember next week. "
                "If unsure, remember it — better to store and clean up later than to forget."
            ),
            "parameters": [
                {
                    "name": "fact",
                    "type": "string",
                    "description": (
                        "The specific information to store. Write it as a self-contained "
                        "sentence someone could read months later and understand. "
                        "BAD: 'user likes Docker'. GOOD: 'User deploys to Fly.io using "
                        "Docker, app listens on port 8080, multi-region enabled.'"
                    ),
                    "required": True,
                },
                {
                    "name": "category",
                    "type": "string",
                    "description": (
                        "What kind of memory: 'preference' (likes/dislikes, workflow), "
                        "'decision' (architecture, tool choices), 'project' (repo names, "
                        "structure), 'person' (name, role, relationship), 'setup' "
                        "(environment, paths, config), 'insight' (lessons, discoveries), "
                        "or 'reference' (URLs, doc links)."
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
                        "Short unique label for this fact (e.g. 'uses-neovim', "
                        "'deploy-target-flyio', 'python-version'). Auto-generated "
                        "from the fact text if you omit it."
                    ),
                    "required": False,
                },
                {
                    "name": "tags",
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Keywords that will help find this later. Include language, "
                        "framework, domain, tool name. E.g. ['python', 'docker', "
                        "'fly.io', 'deployment']."
                    ),
                    "required": False,
                },
                {
                    "name": "importance",
                    "type": "number",
                    "description": (
                        "How critical this is to remember. 1.0 = essential (user's "
                        "name, auth method, core project). 0.5 = nice to know. "
                        "Default 0.7 is right for most facts."
                    ),
                    "required": False,
                    "default": 0.7,
                },
            ],
        },
        {
            "name": "recall",
            "description": (
                "Search everything you have stored in memory. "
                "CALL THIS at the START of every conversation — before you answer "
                "the user's first question, search for their name, their current "
                "project, and any topic keywords in their message. "
                "ALSO CALL when the user asks something you might already know "
                "('what testing framework do I use?', 'what's my deploy setup?'). "
                "Searching first prevents the user from repeating themselves. "
                "Use broad queries ('docker deploy', 'python testing') rather "
                "than exact phrases — the search engine handles fuzzy matching."
            ),
            "parameters": [
                {
                    "name": "query",
                    "type": "string",
                    "description": (
                        "Keywords to search for. Can be a topic ('python deployment'), "
                        "a question fragment ('how do I deploy'), or a person's name. "
                        "Multi-word queries OR the words together — 'docker fly.io' "
                        "matches memories about either."
                    ),
                    "required": True,
                },
                {
                    "name": "limit",
                    "type": "integer",
                    "description": "How many results to return. Use 5 for quick checks, 20 for deep searches.",
                    "required": False,
                    "default": 10,
                },
                {
                    "name": "category",
                    "type": "string",
                    "description": (
                        "Narrow results to one category: 'preference', 'decision', "
                        "'project', 'person', 'setup', 'insight', 'reference'."
                    ),
                    "required": False,
                },
            ],
        },
        {
            "name": "forget",
            "description": (
                "Remove an outdated memory (soft-delete, recoverable). "
                "CALL THIS when the user corrects something you previously remembered. "
                "Examples: 'I don't use Docker anymore, I switched to Kubernetes', "
                "'Actually my name is Thomas, not Tom', 'That deploy target is wrong.' "
                "Always call remember() with the corrected fact right after calling forget(). "
                "The user should not have to repeat a correction in the next conversation."
            ),
            "parameters": [
                {
                    "name": "category",
                    "type": "string",
                    "description": (
                        "The category of the outdated memory (e.g. 'setup', 'preference'). "
                        "Must match exactly what was used when the memory was stored."
                    ),
                    "required": True,
                },
                {
                    "name": "key",
                    "type": "string",
                    "description": (
                        "The key of the outdated memory (e.g. 'deploy-target-flyio'). "
                        "Find this by calling recall() first to locate the memory, "
                        "then pass its key here."
                    ),
                    "required": True,
                },
            ],
        },
        {
            "name": "context",
            "description": (
                "Load a formatted summary of the most important and recent memories, "
                "ready to inject into the current conversation. "
                "CALL THIS at the START of every conversation as a quick alternative "
                "to targeted recall() searches — it gives you the top N memories "
                "across all categories in one call. "
                "Useful when you don't know what to search for yet, or when the user "
                "says something open-ended like 'help me with my project.' "
                "Combine with recall() for best results: context() gives the overview, "
                "recall() drills into specifics."
            ),
            "parameters": [
                {
                    "name": "limit",
                    "type": "integer",
                    "description": (
                        "How many top memories to include. Use 10 for a broad overview, "
                        "5 for a quick session start."
                    ),
                    "required": False,
                    "default": 10,
                }
            ],
        },
        {
            "name": "stats",
            "description": (
                "Return memory database statistics: total memories stored, breakdown "
                "by category and type, database file size. "
                "CALL THIS when the user asks how much you remember, wants to see "
                "what kinds of things are stored, or asks about memory health. "
                "Also useful during debugging to confirm memories are being saved."
            ),
            "parameters": [],
        },
        {
            "name": "health",
            "description": (
                "Quick liveness check — verifies the memory backend is reachable "
                "and responding. CALL THIS if a previous memory tool call failed "
                "or returned an error, to determine whether the backend is down "
                "or the specific operation was the problem."
            ),
            "parameters": [],
        },
    ],
}


# ── Mimir subprocess management ────────────────────────────────────────────

_mimir_proc = None
_mcp_counter = 1
_stdout_queue = None  # queue.Queue fed by the reader thread; None sentinel = EOF

# Per-tool invoke timeout (seconds) for mimir MCP calls.
_MCP_INVOKE_TIMEOUT = 20
# Handshake (initialize) gets a slightly longer leash on cold start.
_MCP_INIT_TIMEOUT = 10


class MemoryUnavailableError(RuntimeError):
    """Raised when the mimir backend is unreachable or times out."""


def _mcp_timeout_s():
    """Return the MCP call timeout in seconds."""
    return _MCP_INVOKE_TIMEOUT


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
        # Startup failure is non-fatal — _mcp_send will attempt a lazy
        # restart on the first invoke call (A-2).
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
