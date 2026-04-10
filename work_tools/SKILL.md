---
name: work-tools
description:
  A collection of AI skills for automating work tasks — Taiga management, Git workflows, and more.
  Uses `docs-cli read-docs <subject>` to load the appropriate context before starting any task.
---

# Skill: work-tools

## How to Use This Skill

Before performing any task, **always load the relevant context** using `docs-cli`:

```bash
docs-cli read-docs <subject>
```

This fetches guidelines, API specs, and environment variables needed for the task.

---

## Subject Routing

Choose the subject based on what the user wants to do:

| User intent | Subject | Command |
|---|---|---|
| Create / update Taiga user stories or tasks | `task-writer` | `docs-cli read-docs task-writer` |
| Look up CLI command usage or options | `api-reference` | `docs-cli read-docs api-reference` |

To see all available subjects at any time:

```bash
docs-cli read-docs --help
```

---

## Workflow

1. **Identify intent** — determine what the user wants to accomplish.
2. **Load context** — run `docs-cli read-docs <subject>` to get the full guideline.
3. **Follow the loaded guideline** — the context returned by `read-docs` contains all instructions, API specs, and examples needed. Do not proceed without loading it first.
