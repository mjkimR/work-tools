# work-tools

A personal collection of AI skills and scripts for automating work tasks.

## 🛠️ Environment

- **OS**: macOS
- **Python**: 3.13+
- **Package Manager**: [uv](https://github.com/astral-sh/uv)

## ⚡ Quick Start

```bash
uv sync
```

## 📁 Project Structure

```
work_tools/
├── SKILL.md                  # Agent skill definition (MCP-style skill manifest)
├── references/               # Markdown-based reference documents for AI context
│   ├── api_spec.md           # CLI tool API specifications
│   ├── feature_guideline.md  # Guidelines for new feature tasks
│   ├── future_task_guideline.md  # Guidelines for future/TODO tasks
│   └── issue_guideline.md    # Guidelines for client issue tasks
└── src/
    ├── core/                 # Core utilities (logging, setup, exceptions)
    ├── modules/
    │   ├── browser/          # Extracts auth tokens and cookies from a running browser
    │   ├── docs/             # read-docs CLI — composes context from references, env vars, and dynamic data
    │   ├── git_repo/         # Git CLI — staged diff, commit history, branch info
    │   ├── ims/              # In-house IMS CLI — document retrieval and comment posting
    │   ├── taiga/            # In-house Taiga CLI — user stories, tasks, and custom attributes
    │   └── workflow/         # Facade layer — orchestrates cross-tool automation workflows
    ├── scripts/              # Standalone utility scripts
    └── util/                 # Shared utility helpers
```

### Module Overview

| Module | Description |
|---|---|
| `browser` | Extracts auth tokens and cookies from a running browser (e.g. Chrome) for authenticated API calls |
| `docs` | composes contextual information from references, env vars, and dynamic data for AI consumption |
| `git_repo` | Git CLI — staged diff, recent commit history, and branch info for AI-assisted workflows |
| `ims` | In-house IMS CLI — document retrieval (single/bulk), comment posting via browser cookie auth |
| `taiga` | In-house Taiga CLI — user story/task management, status queries, and custom attributes |
| `workflow` | Facade layer — orchestrates cross-tool automation (e.g. full context retrieval, one-shot US creation) |
