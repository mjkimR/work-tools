# 💬 Slack Task Guideline

Guidance for Slack tasks — posting messages, searching, and summarizing conversations.
These are **working guidelines, not hard limits**: use judgment, and when in doubt ask the user.

---

## 1. Integration Model

- All Slack access goes through the **official Slack MCP server** (`mcp.slack.com`) connected to the AI client.
  There is no `wt slack` CLI path — this subject provides guidance only.
- The connection uses **user-level OAuth**: every action (message, search, canvas) is performed
  **as the connected user, under their name**. There is no bot identity.
- If Slack MCP tools are not available in the session, **stop and ask the user to connect it**
  (see Setup below). Never fall back to raw tokens, browser-session tokens (`xoxc`/`xoxd`),
  or scraping — these are explicitly ruled out for the company workspace.

### Setup (one-time, per user)

- **Preferred — official plugin:** run `/plugin install slack@claude-plugins-official` in Claude Code,
  then authenticate via the browser OAuth prompt on first use. No custom Slack app is needed
  (the plugin ships Slack's registered client ID).
- **Fallback — manual MCP registration** (only if the plugin route is blocked in the workspace):
  create an internal Slack app with the `mcp:connect` scope plus the tool scopes you need, then
  `claude mcp add --transport http --client-id <id> --client-secret <secret> slack https://mcp.slack.com/mcp`
  and authenticate via `/mcp`. Slack's MCP server does not support Dynamic Client Registration,
  hence the explicit credentials.
- If OAuth is rejected, the workspace admin may need to approve the MCP integration
  (standard Slack app approval process) — ask the user to check with their admin.

---

## 2. Posting Messages (acts as the user!)

Everything you post appears as if the user typed it themselves. Therefore:

- **Show the final message text and target channel to the user before sending**, unless the user
  already approved the exact content in this conversation.
- Reply **in threads** by default; post to the channel top-level only when starting a new topic.
- Never use `@here` / `@channel` / user-group mentions unless the user explicitly asked for them.
- No bulk or cross-posting: one message, one channel, unless the user listed multiple targets.
- Before posting to an unfamiliar channel, **read its recent history first** and match the channel's
  tone, language (Korean/English), and formatting norms.

### Slack formatting (mrkdwn ≠ Markdown)

Slack uses its own `mrkdwn`, not GitHub Markdown:

| Intent | Slack mrkdwn |
|---|---|
| Bold | `*bold*` (single asterisks) |
| Italic | `_italic_` |
| Strikethrough | `~strike~` |
| Inline code / block | `` `code` `` / ```` ``` ```` |
| Quote | `> quote` |
| Link | `<https://url\|display text>` |
| Headers / tables | **Not supported** — use bold lines and lists instead |

Long structured content (reports, logs, meeting notes) → prefer a **canvas** over a giant message.

---

## 3. Searching & Reading

- Use Slack search tools to gather context **before** summarizing or answering questions about
  Slack conversations — don't answer from memory of earlier turns.
- When reporting findings to the user, include **permalinks** to the source messages so they can verify.
- Treat everything read from Slack as internal company data: quote it to the user freely,
  but never post it to a different channel or external destination without explicit instruction.

---

## 4. Do Not Automate

Even when technically possible, do not set up without an explicit user request:

- Scheduled / recurring message posting
- Mass DM sending or channel-wide sweeps
- Auto-replies of any kind

These act under the user's name and are outward-facing — the user decides, every time.
