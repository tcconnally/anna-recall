# Anna Platform Submission — Step by Step

## What's ready

- ✅ PyInstaller binary built (12MB, self-contained, mimir bundled)
- ✅ GitHub Release v1.0.0: https://github.com/tcconnally/anna-recall/releases/tag/v1.0.0
- ✅ Download URL: https://github.com/tcconnally/anna-recall/releases/download/v1.0.0/mimir-memory-linux-x86_64.tar.gz
- ✅ SHA256: b3cf36ef7c1612f657b2519c75a04bd613d3cb5cb8f65024ef64756ec1baf6f8

---

## Step 1: Create the Executa on Anna

Go to Anna Developer Console → Executa → My Tools → Create Tool

1. **Name:** `mimir-memory`
2. **Type:** `tool`
3. **Click 🪪 Mint** next to the Tool ID field — copy the minted ID, it'll look like `tool-{you}-mimir-memory-{abc123}`
4. **Paste this tool_id back to me** so I can update the App manifest

**Distribution:**
- Type: `binary`
- For `linux-x86_64`:
  - URL: `https://github.com/tcconnally/anna-recall/releases/download/v1.0.0/mimir-memory-linux-x86_64.tar.gz`
  - SHA256: `b3cf36ef7c1612f657b2519c75a04bd613d3cb5cb8f65024ef64756ec1baf6f8`
  - Entrypoint: `mimir-memory`
  - Format: `tar.gz`
- For `darwin-arm64` and other platforms: leave empty for now (we only built Linux)

**Manifest:** Paste the describe output. Open in your terminal:
```bash
curl -L https://github.com/tcconnally/anna-recall/releases/download/v1.0.0/mimir-memory-linux-x86_64.tar.gz | tar xz
echo '{"jsonrpc":"2.0","id":1,"method":"describe"}' | ./mimir-memory 2>/dev/null | python3 -c "import sys,json; print(json.dumps(json.loads(sys.stdin.readline())['result'], indent=2))"
```
Or just paste the raw manifest from `/executas/mimir-memory/mimir_memory_plugin.py` (the MANIFEST dict, lines ~30-263).

**Visibility:** `app_bundled` (so it's only installable through the App, not public)

**Capabilities:** 
- Logo URL: leave empty for now
- README: paste from our README.md
- Sample prompts:
  ```
  Remember that the user prefers pytest over unittest
  What testing framework does this user prefer?
  Show me everything you remember about this user
  ```

5. Click **Create** to publish the Executa

---

## Step 2: Create the Anna App

Go to Anna Developer Console → Apps → Create App

**Listing:**
- Name: `Recall — Persistent Memory for Anna`
- Slug: `recall`
- Category: `productivity`
- Tagline: `Never ask twice. Persistent, searchable memory that follows you across every conversation.`
- Description: (paste from `demo/submission_text.md`)

**Version 1.0.0 Manifest:**
- Create a new version
- Paste the manifest from `manifest.json` — BUT replace the tool_id:
  - Find: `"tool-dev-mimir-memory"` 
  - Replace with: the real minted tool_id from Step 1 (e.g. `"tool-tcconnally-mimir-memory-abc123"`)
  - Do this in all THREE places it appears (required_executas, ui.host_api.tools)

**UI Bundle:**
- Upload `bundle/index.html` and `bundle/app.js` via the bundle pipeline
- After uploading, finalize the bundle

**Validate:** Click Validate — should return `valid: true`

6. Click **Create Version**

---

## Step 3: Submit for Review

Settings tab → **Submit for Review**

This puts the app in `PENDING_REVIEW`. The Anna team will review and approve.

---

## Step 4: After Approval

Versions tab → **Publish** version 1.0.0

The app becomes visible in the App Store. Install it yourself and test end-to-end.

---

## Early Feedback Deadline

Submit v1 before **Friday June 19 EOD ET** to get official feedback from the Anna team.

---

## Troubleshooting

**If describe times out:** The mimir binary inside the PyInstaller package takes ~2s to extract and start. Anna's 5s timeout should handle this. If it fails, the binary is too large — we can slim it down.

**If install fails:** Check the install logs in Anna Developer Console → Executa → My Tools → click the tool → Install Logs.

**If the tool shows "Stopped":** The plugin process exited. This is the #1 common bug. Our plugin loops on stdin until EOF — it should stay alive. If it dies, check stderr in the logs.
