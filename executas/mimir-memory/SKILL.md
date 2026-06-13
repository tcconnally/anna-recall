---
name: memory-hygiene
description: "How to use persistent memory effectively — when to remember, what to store, and how to recall the right context at the right time."
metadata: {"matrix":{"emoji":"🧠","execution_mode":"prompt","category_name":"productivity"}}
---

# Recall — Memory Hygiene for Anna

You have access to persistent memory through the Recall toolset. This means
you can remember things across conversations — user preferences, decisions,
project context, and learned facts.

Good memory hygiene makes you dramatically more useful. Poor memory hygiene
makes you annoying (remembering trivia) or useless (remembering nothing).

## When to Remember

Store a memory when:

1. **User shares a preference** — "I prefer tabs over spaces", "Always use pytest"
2. **A decision is made** — "Let's deploy to AWS", "We'll use Postgres 16"
3. **Project context is shared** — repo names, architecture choices, team structure
4. **Setup/configuration is described** — "My home directory is X", "I use Python 3.12"
5. **The user corrects you** — store the correction so you don't repeat the mistake
6. **Insights emerge** — you solved a tricky bug, found a better approach

## What NOT to Store

- Transient conversation details (today's weather query)
- Things the user explicitly says not to remember
- Speculation or guesses — only confirmed facts
- Duplicates — check recall() first if unsure

## How to Use Recall

### At conversation start
Call `recall(query="<user's name or topic>", limit=5)` to load relevant context.
This is the single highest-impact thing you can do. If you know the user's name,
search for it. If the conversation has a clear topic, search for that.

### When the user shares something important
Call `remember(fact="...", category="...")` immediately. Be specific:
- BAD: `remember(fact="user likes Python")`
- GOOD: `remember(fact="User uses Python 3.12 with uv for package management", category="preference", tags=["python", "tooling"])`

### When you're unsure
Call `recall(query="...")` to check what you already know before asking the user
to repeat themselves. The whole point is reducing friction.

### For corrections
If remembering a correction, also call `forget()` on the outdated memory.

## Memory Categories

| Category | Use for |
|----------|---------|
| `preference` | User likes/dislikes, workflow choices |
| `decision` | Architecture decisions, tool choices |
| `project` | Repo names, project structure, URLs |
| `person` | Names, roles, relationships |
| `setup` | Environment, installed tools, paths |
| `insight` | Discoveries, lessons learned, bug fixes |
| `reference` | URLs, API keys (warn user!), docs links |

## Tips

- **Be specific.** "User deploys to fly.io with Docker, app runs on port 8080" beats "user uses Docker"
- **Tag liberally.** Tags make recall() more effective. Include language, framework, domain.
- **Set importance.** Default 0.7. Bump to 0.9-1.0 for critical facts (name, auth setup). 
- **Use keys consistently.** If you store with key `deploy-target`, recall it with the same category/key pair.
- **The context() call** gives you a summary of top memories — use it at session start for a quick overview.
