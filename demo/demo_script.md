# Recall Demo Script — 90 Seconds

## Screen layout during recording

- Full screen, 1920x1080
- Split: Anna chat on left 55%, Recall dashboard on right 45%
- Dark mode throughout
- Cursor visible, move deliberately
- No music, clean voiceover

---

## 0:00-0:10 — The Problem

**Show:** Anna chat window, empty new conversation

**Say:** "AI agents are great. But every time you start a new conversation, you start from zero. They don't remember your name, your preferences, or what you decided last time."

---

## 0:10-0:25 — One Click Install

**Show:** Type `#recall` in the Anna chat input, hit enter. The Recall app activates.

**Say:** "Recall fixes that. It's an Anna app that gives your agent persistent memory. Install once, mention it in any conversation, and your agent remembers."

**Show:** The "Recall installed" confirmation or system message. The agent responds with a greeting acknowledging it has memory access.

---

## 0:25-0:55 — Memory In Action (Conversation 1)

**Show:** Type the following messages, one at a time. Let the agent respond naturally to each.

**Type:** "Hey, a few things about me: my name is Thomas. I build AI tools — I'm working on a project called Perseus that injects context into LLM prompts. I deploy everything to Fly.io with Docker. Oh, and I strongly prefer pytest over unittest, with xdist for parallel tests."

**Show:** The agent responds, calling `remember()` multiple times in the background. (If Anna shows tool calls, let them be visible briefly.)

**Say:** "The agent automatically identifies what's worth remembering — my name, my project, my deployment setup, my testing preferences. I didn't ask it to remember anything. It just knows what matters."

**Show:** Hover over or highlight the tool calls if visible. Type next message.

**Type:** "Actually I forgot — I also use uv for Python package management, not pip."

**Say:** "It even handles corrections. The agent updates what it knows without me having to manage anything."

---

## 0:55-1:20 — The Payoff (Conversation 2)

**Show:** Start a fresh conversation. Blank slate.

**Type:** "What testing framework should I use for this new project?"

**Say:** "Now watch. New conversation, no context. But the agent recalls what it knows about me."

**Show:** The agent responds: "Based on what I know, you prefer pytest with xdist for parallel test execution. You also use uv for package management, so you'd want to set up your pyproject.toml with pytest as a dev dependency."

**Say:** "It remembered my preference from a completely different conversation. It even connected the dots — since I use uv, it suggested the uv-specific setup. That's the difference between a chatbot and an agent that actually knows you."

---

## 1:20-1:30 — Dashboard + Outro

**Show:** Click to open the Recall dashboard. The UI shows memory stats and the stored facts.

**Say:** "And there's a dashboard where you can browse and search everything that's been stored. Recall is built on Mimir, an open-source memory backend. Zero config, works out of the box."

**Show:** GitHub repo URL on screen.

**Say:** "One install. Never ask twice. Recall — persistent memory for Anna."

---

## Exact Prompts (copy-paste into Anna during recording)

### Conversation 1:
```
#recall Hey, a few things about me: my name is Thomas. I build AI tools — I'm working on a project called Perseus that injects context into LLM prompts. I deploy everything to Fly.io with Docker. Oh, and I strongly prefer pytest over unittest, with xdist for parallel tests.
```

### Conversation 1 (follow-up):
```
Actually I forgot — I also use uv for Python package management, not pip.
```

### Conversation 2 (new conversation):
```
#recall What testing framework should I use for this new project?
```

---

## Recording Setup

1. Open Anna (desktop or web)
2. Start Recall dashboard in split view: `anna-app dev` and open the dashboard URL
3. Screen recorder: OBS or macOS QuickTime screen recording
4. Resolution: 1920x1080
5. Audio: Clean voiceover, no background noise
6. Record in one take — no editing needed if the flow is right

## Post-Recording

1. Trim start/end
2. Add title card at 0:00: "Recall — Persistent Memory for Anna"
3. Add GitHub URL overlay at 1:27
4. Export as MP4, upload to YouTube (unlisted)
