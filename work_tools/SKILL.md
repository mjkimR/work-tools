---
name: work-tools
description:
  Use this skill only when the user explicitly asks to use work-tools, the `wt` CLI, Taiga/workflow automation,
  or one of its documented quick commands such as `import-ims`, `sync-context`, `sync-git`, or `gen-commit`.
  Do not use this skill for general coding, Git, debugging, explanation, or loosely related work tasks.
---

# Skill: work-tools

## Activation Rule

Only use this skill when the user explicitly requests work-tools, the `wt` CLI, Taiga/workflow automation,
or one of the documented quick commands.

Do not use this skill for nearby, loosely related, or general software engineering tasks.

## 💡 Core Strategy: Prioritize Workflow CLI

Always prioritize **`wt workflow`** commands for complex, multi-step, or cross-module tasks (e.g., getting full user
story context).
Use granular tools (`wt taiga`, `wt ims`, `wt git`) **only** when a suitable `wt workflow` command does not exist or when
specific fine-grained control is explicitly required.

---

## How to Use This Skill

Before performing any task, **always load the relevant context** using `wt docs`:

```bash
wt docs read-docs <subject>
```

This fetches guidelines, API specs, and environment variables needed for the task.

**Read the output in full.** Do not pipe it through `head`, `tail`, `sed -n`, or any other
truncation. The normative parts — description templates, custom-field IDs and their allowed
dropdown values — sit *after* the general instructions, so a truncated read reliably drops
exactly the parts that must be obeyed.

---

## ⚠️ Command Execution

- **Simply execute `wt` CLI commands directly from any workspace directory.**
- Do NOT switch the command execution directory (CWD) to the `work-tools` repository. Run `wt` from the active target workspace.
- The `wt` tool will automatically resolve its `.env` settings and dependencies globally.
- Let the `wt` CLI automatically target the configured repository (via `GIT_TARGET_REPO`) from the `work-tools` root.
- **Do NOT import `work_tools` library modules directly (e.g., using `python -c "from work_tools.modules... import ..."`) to call internal APIs.** Doing so bypasses the CLI entrypoint path setup, preventing the `.env` configuration from loading and causing errors like `ValueError: Project ID is not set`. Always invoke the `wt` CLI directly.

---

## Subject Routing

Choose the subject based on the user's intent:

- **task-writer**: Use when creating or updating Taiga user stories, tasks, or managing project status.
    - Command: `wt docs read-docs task-writer`
- **api-reference**: Use when looking up CLI command usage, options, or Quick Command recipes.
    - Command: `wt docs read-docs api-reference`
- **slack**: Use when posting to Slack, searching Slack messages, or summarizing Slack conversations.
    - Command: `wt docs read-docs slack`
    - Note: Slack actions run through the **official Slack MCP server** (not `wt` CLI) — this subject loads working guidelines only.

To see all available subjects at any time:

```bash
wt docs read-docs --help
```

---

## Quick Commands

This skill supports shortcut workflows (Quick Commands). When you encounter these patterns, follow the specific routing:

- **`import-ims <url>`**
    - **Goal**: Create a structured Taiga User Story from an IMS document URL.
    - **Action**: Load **`task-writer`** (`wt docs read-docs task-writer`) to retrieve the conversion recipe.
- **`sync-context #ref`**
    - **Goal**: Smartly synchronize and refresh the full context (US, Tasks, Comments, IMS) of a User Story.
    - **Action**: Load **`task-writer`** (`wt docs read-docs task-writer`) to retrieve the synchronization logic.
- **`sync-git #ref`**
    - **Goal**: Analyze Git branch/staged changes and update the development progress of a Taiga User Story.
    - **Action**: Load **`task-writer`** (`wt docs read-docs task-writer`) to retrieve the Git-to-Taiga mapping guide.
- **`gen-commit`**
    - **Goal**: Generate high-quality, conventional commit messages based on staged changes and history.
    - **Action**: Load **`api-reference`** (`wt docs read-docs api-reference`) to retrieve the commit style guide and instructions.

---

## Workflow

1. **Identify intent** — determine what the user wants to accomplish.
2. **Select Tool Strategy** — check if `wt workflow` can handle the request in one go.
3. **Load context** — run `wt docs read-docs <subject>` and read the output in full, untruncated.
   Do not proceed without loading it first.
4. **Declare the guideline** — for Taiga writes, say which guideline you are applying
   (`issue` / `feature` / `future_task`) before writing anything. Picking one is a decision;
   skipping the decision is how templates get blended.
5. **Copy the template, don't reference it** — paste that guideline's `###` headings verbatim,
   then fill them in. Do not add, drop, rename, or reorder sections. Keep empty sections and
   write "해당 없음".
6. **Route the overflow** — content that does not fit the template goes to a **custom field**
   or `--comment`. It is never a reason to grow the description body.

> Steps 4–6 exist because "follow the loaded guideline" is too abstract to act on. Having read a
> template is not the same as having used it: the failure mode in practice is reading it, then
> letting the material at hand dictate a different structure.
