---
name: work-tools
description:
  A collection of AI skills for automating work tasks — Taiga management, Git workflows, and more.
  Uses `wt docs read-docs <subject>` to load the appropriate context before starting any task.
---

# Skill: work-tools

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

---

## Subject Routing

Choose the subject based on the user's intent:

- **task-writer**: Use when creating or updating Taiga user stories, tasks, or managing project status.
    - Command: `wt docs read-docs task-writer`
- **api-reference**: Use when looking up CLI command usage, options, or Quick Command recipes.
    - Command: `wt docs read-docs api-reference`

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
3. **Load context** — run `wt docs read-docs <subject>` to get the full guideline.
4. **Follow the loaded guideline** — the context returned by `read-docs` contains all instructions, API specs, and
   examples needed. Do not proceed without loading it first.
