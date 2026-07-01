# DoraHacks Submission — Copy-Paste Ready

## Project Name
Recall — Persistent Memory for Anna

## Elevator Pitch (one line)
Never ask twice. Persistent, searchable memory that follows you across every Anna conversation.

## What It Does (full description)

Most AI chat platforms are stateless — the agent forgets everything when the conversation ends. Recall fixes this with a single `#mention`.

**The agent automatically:**
- Remembers your preferences, decisions, and project context as you chat
- Recalls relevant information at the start of every new conversation
- Corrects outdated info when you provide updates
- Categorizes and tags memories for fast retrieval

**You get a dashboard** where you can browse, search, and manage everything that's been stored. No configuration, no manual tagging — the AI handles memory hygiene on its own.

Built on **Mneme**, a battle-tested persistent memory backend with SQLite + FTS5 full-text search. Real persistence, not a mock.

## How It Uses AI

The agent (Anna's LLM) acts as an intelligent memory curator:

- **Decides what's worth remembering** — not every message, only preferences, decisions, facts, and context that will matter later
- **Categorizes and tags** memories for better future retrieval
- **Detects corrections** — when the user updates outdated info, the agent updates or removes the old memory
- **Recalls proactively** — at the start of every conversation, it searches memory for relevant context before answering

This isn't a dumb CRUD wrapper. The AI is the curator.

## How It Connects to Anna

Recall uses all three Anna building blocks:

1. **Executa Tool** (`mimir-memory`) — Python plugin speaking JSON-RPC over stdio, exposing six tools: `remember`, `recall`, `forget`, `context`, `stats`, `health`
2. **SKILL.md** — Declarative skill teaching the agent memory hygiene: when to remember, what to store, how to recall, when to forget
3. **Anna App UI** — Dashboard built with the Anna App Runtime SDK, showing memory stats, search, and browse

## Why It's Useful

Every Anna user has experienced the frustration of reintroducing themselves. Developers, researchers, project managers — anyone who uses Anna regularly wants it to get smarter over time. Recall delivers that with zero friction.

## Built With

- **Python** — Executa plugin proxying Anna JSON-RPC calls to Mneme
- **Mneme** (Rust) — Open-source persistent memory backend
- **Anna Executa Protocol** — JSON-RPC 2.0 over stdio
- **Anna App Runtime SDK** — Host API for tool invocation
- **Vanilla HTML/CSS/JS** — Dashboard UI

## Try It

```bash
# Prerequisites: Mneme installed (github.com/tcconnally/mimir)
npm i -g @anna-ai/cli
git clone https://github.com/tcconnally/anna-recall
cd anna-recall
anna-app dev
# Open http://localhost:5180
```

## Repository
https://github.com/tcconnally/anna-recall

## Demo Video
[YouTube link here]
