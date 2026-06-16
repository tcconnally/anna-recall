# Recall Demo Script — "Before & After" (90 seconds)

## Structure
- 0:00-0:15 — THE FRUSTRATION (Before)
- 0:15-0:40 — THE MAGIC (After, conversation 1)
- 0:40-0:70 — THE PAYOFF (After, conversation 2)
- 0:70-0:90 — THE DASHBOARD + Outro

---

## 0:00-0:15 — THE FRUSTRATION

**Show:** Anna chat, blank conversation. No `#recall` mention.

**Type:** "Hey, what testing framework should I use for my Python project?"

**Anna responds:** Generic advice — "You should consider pytest or unittest, depending on your needs..."

**Say:** "This is every AI chat today. It doesn't know me. It doesn't know I've been using pytest for years. Every conversation starts from zero."

---

## 0:15-0:40 — ONE MENTION CHANGES EVERYTHING

**Show:** Type `#recall` then the message.

**Type:** "#recall Hey, a few things about me: my name is Thomas. I'm building an AI tool called Perseus. I deploy to Fly.io with Docker. And I strongly prefer pytest over unittest — I use xdist for parallel tests."

**Anna responds:** "Got it Thomas — I'll remember that. You're working on Perseus, deploying to Fly.io with Docker, and you use pytest with xdist. Let me know what you need."

**Show:** The dashboard in split view. The stats counter ticks up. The "Just saved" indicator pulses green.

**Say:** "One mention, and the agent starts building a memory of who I am. Notice — it confirms what it saved in one natural sentence. Not a dialog. Not an interruption. Just acknowledgment. The dashboard shows it happening in real-time."

---

## 0:40-0:70 — THE PAYOFF

**Show:** Start a completely fresh conversation. Blank slate.

**Type:** "#recall What testing framework should I use?"

**Anna responds:** "Based on what you told me earlier, you prefer pytest with xdist for parallel test execution. Since you deploy to Fly.io with Docker, I'd set up your CI to run tests in a container matching your production environment."

**Say:** "New conversation. No context. But Anna knows me. It recalled my testing preference AND connected it to my deployment setup — because that's what a memory system should do. Connect dots across conversations."

---

## 0:70-0:90 — THE DASHBOARD + OUTRO

**Show:** Click to open the Recall dashboard. Show stats, show the search bar, type "pytest" — results appear instantly.

**Say:** "Every memory is browsable. Every recall is transparent. The user is always in control. Recall — one install, and Anna never asks twice."

**Show:** GitHub URL on screen.

---

## Exact Prompts (copy-paste)

### "Before" (no Recall):
```
What testing framework should I use for my Python project?
```

### Conversation 1 (with Recall):
```
#recall Hey, a few things about me: my name is Thomas. I'm building an AI tool called Perseus. I deploy to Fly.io with Docker. And I strongly prefer pytest over unittest — I use xdist for parallel tests.
```

### Conversation 2 (fresh):
```
#recall What testing framework should I use?
```

### Dashboard search:
```
pytest
```

---

## Recording Notes

- Record both conversations back-to-back in one take
- Use split view: Anna chat on left, Recall dashboard on right
- Let the "Just saved" animation play out naturally (it auto-refreshes every 15s)
- No music. Clean voiceover. Natural pace.
- The "Before" section should feel frustrating. The "After" should feel magical.
