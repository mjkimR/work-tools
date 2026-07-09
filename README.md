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

Then set up the `.env` file (see [Environment Variables](#-environment-variables) below).

## 🔑 Environment Variables

The `.env` file is generated interactively via the unified CLI:

```bash
uv run wt init
```

The command will:
1. Connect to Taiga via your open Chrome session and list available projects
2. Ask you to select a project ID
3. Collect Git settings (`GIT_USER_EMAIL`, `GIT_TARGET_REPO`)
4. Write everything to `.env` at the project root

> **Prerequisite**: Chrome must have the Taiga site open and logged in before running the script.

> **Note**: Taiga custom attributes are *not* written to `.env`. They are resolved from the
> Taiga API at runtime, so adding or changing an attribute needs no `.env` rebuild.
> Run `wt docs read-docs task-writer` to see the current IDs and allowed values.

## 🖥️ CLI Usage

The project uses a unified CLI entry point `wt`.

```bash
uv run wt --help
```

See [`work_tools/references/api_spec.md`](work_tools/references/api_spec.md) for the full command reference.

> `api_spec.md` is auto-generated. To regenerate:
> ```bash
> uv run wt dev gen-spec
> ```

## 📁 Project Structure

```
work_tools/
├── SKILL.md                  # Agent skill router — routes tasks to the right read-docs subject
├── references/               # Markdown-based reference documents for AI context
│   ├── api_spec.md               # CLI tool API specifications (auto-generated)
│   ├── task_writer_guideline.md  # Detailed instructions for Taiga task management
│   ├── feature_guideline.md      # Guidelines for new feature tasks
│   ├── future_task_guideline.md  # Guidelines for future/TODO tasks
│   └── issue_guideline.md        # Guidelines for client issue tasks
└── src/
    └── work_tools/           # Main package
        ├── main.py           # Unified CLI entry point (wt)
        ├── core/             # Core utilities (logging, setup, exceptions)
        ├── modules/
        │   ├── browser/      # Extracts auth tokens and cookies from a running browser
        │   ├── docs/         # read-docs CLI — composes context from references, env vars, and dynamic data
        │   ├── git_repo/     # Git CLI — staged diff, commit history, branch info
        │   ├── ims/          # In-house IMS CLI — document retrieval and comment posting
        │   ├── taiga/        # In-house Taiga CLI — user stories, tasks, and custom attributes
        │   └── workflow/     # Facade layer — orchestrates cross-tool automation workflows
        ├── scripts/          # Utility scripts and CLI subcommands
        └── util/             # Shared utility helpers
```

### Module Overview

| Module     | Description                                                                                           |
|------------|-------------------------------------------------------------------------------------------------------|
| `browser`  | Extracts auth tokens and cookies from a running browser (e.g. Chrome) for authenticated API calls     |
| `docs`     | composes contextual information from references, env vars, and dynamic data for AI consumption        |
| `git_repo` | Git CLI — staged diff, recent commit history, and branch info for AI-assisted workflows               |
| `ims`      | In-house IMS CLI — document retrieval (single/bulk), comment posting via browser cookie auth          |
| `taiga`    | In-house Taiga CLI — user story/task management, status queries, and custom attributes                |
| `workflow` | Facade layer — orchestrates cross-tool automation (e.g. full context retrieval, one-shot US creation) |
