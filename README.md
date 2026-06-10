# Recall — Persistent Memory for Anna

**Never ask twice.** Recall gives Anna agents long-term memory across conversations.

Built on [Mimir](https://github.com/tcconnally/mimir), a battle-tested persistent memory backend for AI agents.

## How It Works

1. **Install Recall** from the Anna App Store (or run locally)
2. **#mention Recall** in any Anna conversation
3. The agent automatically:
   - Recalls relevant context at conversation start
   - Remembers preferences, decisions, and facts you share
   - Forgets outdated info when you correct it
4. Open the **Recall dashboard** to browse and search your memory

## Features

- **Auto-memory** — the agent decides what's worth remembering; you don't manage it
- **Full-text search** — find anything by keyword, category, or topic
- **Smart decay** — important memories stick; stale ones fade
- **Visual dashboard** — browse, search, and manage memories in the app UI
- **Zero config** — works out of the box with Mimir's defaults

## Architecture

```
Anna Chat → #mention Recall
               ↓
         manifest.json     prompt addendum injected
               ↓
    ┌──────────────────────────────────┐
    │  mimir-memory Executa (Python)    │
    │  JSON-RPC over stdio              │
    │  ┌────────────────────────────┐   │
    │  │  remember / recall / forget │   │
    │  │  context / stats / health   │   │
    │  └──────────┬─────────────────┘   │
    └─────────────┼─────────────────────┘
                  ↓
    ┌──────────────────────────────────┐
    │  Mimir (Rust)                     │
    │  MCP JSON-RPC server              │
    │  SQLite + FTS5 full-text search   │
    └──────────────────────────────────┘
                  ↓
          recall.db (SQLite)
```

## Project Structure

```
anna-recall/
├── manifest.json              # Anna App manifest (schema 2, UI + tools)
├── app.json                   # App Store listing metadata
├── bundle/
│   ├── index.html             # Memory dashboard UI
│   └── app.js                 # Anna SDK bootstrap
├── executas/
│   └── mimir-memory/
│       ├── mimir_memory_plugin.py   # Executa tool (JSON-RPC → Mimir proxy)
│       ├── SKILL.md                 # Memory hygiene skill for the agent
│       └── pyproject.toml           # Python project config
├── docs/
│   └── SUBMISSION.md          # Hackathon submission text
└── README.md
```

## Quick Start (Local Dev)

**Prerequisites:**
- Node 22+, uv (Astral), [Mimir](https://github.com/tcconnally/mimir) installed
- `npm i -g @anna-ai/cli`

```bash
# Clone and enter
git clone https://github.com/tcconnally/anna-recall.git
cd anna-recall

# Start dev harness
anna-app dev

# Open http://localhost:5180
```

## Hackathon

Built for the **Anna AI-Native App Hackathon** (Jun 15–22, 2026).

**One idea:** Most AI chat platforms forget everything between conversations. Recall fixes that with a single #mention.

**Built with:** Python, Mimir, Anna Executa protocol, vanilla HTML/CSS/JS.

## License

MIT — see [LICENSE](LICENSE)
