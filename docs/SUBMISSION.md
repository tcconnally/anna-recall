# Hackathon Submission — Anna AI-Native App Hackathon

## Project Name
**Recall — Persistent Memory for Anna**

## Elevator Pitch
Recall gives Anna agents long-term memory so you never have to repeat yourself. One #mention, and the agent remembers your preferences, decisions, and context across every conversation.

## What It Does
Most AI chat platforms are stateless — the agent forgets everything when the conversation ends. Recall fixes this with a single Anna App:

- **Automatic memory** — The agent uses the `remember` tool to store preferences, decisions, project context, and important facts as they come up
- **Context-aware recall** — At the start of every conversation, the agent searches memory for relevant context about the user
- **Memory hygiene** — A SKILL.md teaches the agent *what* to remember, *when* to recall, and how to keep memory clean (forgetting outdated info)
- **Visual dashboard** — An App UI lets users browse, search, and manage their memory store directly

## Who It's For
Every Anna user who's tired of reintroducing themselves. Developers, researchers, project managers — anyone who uses Anna regularly and wants it to get smarter over time.

## How AI Is Used
The agent (Anna's LLM) makes intelligent decisions about what to store:
- It identifies preferences, decisions, and important context in conversation
- It categorizes and tags memories for better retrieval
- It decides when to recall relevant context before answering
- It detects and corrects outdated information

This isn't a dumb CRUD wrapper — the AI is the memory curator.

## How It Connects to Anna
Recall uses all three Anna building blocks:

1. **Executa Tool** (`mimir-memory`) — A Python plugin speaking JSON-RPC over stdio that exposes 6 tools: `remember`, `recall`, `forget`, `context`, `stats`, `health`
2. **SKILL.md** — A declarative skill teaching the agent memory hygiene (when to remember, what to store, how to recall)
3. **Anna App UI** — A dashboard (`bundle/index.html`) using the Anna App Runtime SDK to display memory stats and search results

The app manifest (`manifest.json`) bundles all three with a system prompt addendum that activates the memory behavior when the user `#mention`s Recall.

## Built With
- **Python** — Executa plugin (mimir-memory) proxying Anna's JSON-RPC calls to Mneme
- **Mneme** (Rust) — Battle-tested persistent memory backend with SQLite + FTS5 full-text search
- **Anna Executa Protocol** — JSON-RPC 2.0 over stdio, `describe`/`invoke`/`health` methods
- **Anna App Runtime SDK** — Host API for tool invocation and window management
- **Vanilla HTML/CSS/JS** — Memory dashboard UI with real-time search and stats

## Demo
[Video link here]

## Repository
https://github.com/tcconnally/anna-recall

## Try It
1. `npm i -g @anna-ai/cli`
2. Install Mneme: https://github.com/tcconnally/mimir
3. `git clone https://github.com/tcconnally/anna-recall && cd anna-recall`
4. `anna-app dev`
5. Open http://localhost:5180
