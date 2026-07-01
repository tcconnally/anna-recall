# Anna Recall — Persistent Memory Plugin for Anna AI

**435 lines. Production memory engine. Never ask twice.**

Anna Recall is a 435-line plugin that gives Anna AI persistent memory across sessions. It's thin because [Perseus Vault](https://github.com/Perseus-Computing-LLC/perseus-vault) does the heavy lifting — a tested Rust engine with FTS5 keyword search, confidence decay, and structured entity storage. One plugin install, one config line, and Anna remembers everything you've told her.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Anna AI App](https://img.shields.io/badge/Anna%20AI-App%20Store-purple)]()

## The Pitch

> *"This plugin is 435 lines because the heavy lifting is a tested Rust engine. Production memory engine, 15/15 tests, hackathon-speed integration."*

| Stat | Value |
|---|---|
| Plugin size | 435 lines |
| Engine tests | 15/15 passing |
| Backend | Perseus Vault (Rust, SQLite + FTS5) |
| Setup | 1 config line |

## The Demo Arc

```
Session 1  →  You tell Anna your name, project, preferences, and a recurring bug.
                ↓
Kill Anna  →  Terminate the process. All session state lost — except what Perseus Vault stored.
                ↓
Session 2  →  Anna greets you by name, knows your project, remembers the bug. 
              Zero re-orientation.
```

That's the whole value proposition in 3 steps.

## Architecture

```
Anna Chat → #mention Recall
               ↓
         manifest.json     (prompt addendum injected)
               ↓
    ┌──────────────────────────────────┐
    │  mimir-memory Executa (Python)   │
    │  JSON-RPC over stdio             │
    │  remember / recall / forget       │
    └──────────────┬───────────────────┘
                   ↓
    ┌──────────────────────────────────┐
    │  Perseus Vault (Rust)            │
    │  MCP server, SQLite + FTS5       │
    │  15/15 production tests          │
    └──────────────┬───────────────────┘
                   ↓
           recall.db (SQLite)
```

## Features

- **Auto-memory** — the agent decides what's worth remembering; you don't manage it
- **Full-text search** — find anything by keyword, category, or topic (FTS5)
- **Smart decay** — important memories stick; stale ones fade (configurable half-lives)
- **Visual dashboard** — browse, search, and manage memories in the app UI
- **Zero config** — works out of the box with Perseus Vault's defaults

## Quick Start

```bash
# Install from Anna App Store
anna plugins install anna-recall

# Configure — one line points at Perseus Vault
# anna-config.yaml:
plugins:
  recall:
    backend: mimir
    db_path: ~/.mimir/data/mimir.db
```

## Hackathon

Built for the **Anna AI-Native App Hackathon** (Jun 15–22, 2026).

## License

MIT — see [LICENSE](LICENSE)

---

[Website](https://perseus.observer/anna-recall/) · [Perseus Vault](https://github.com/Perseus-Computing-LLC/perseus-vault)
