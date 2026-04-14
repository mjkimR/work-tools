# Task Writer Guideline

Detailed instructions for managing Taiga user stories and tasks via CLI.

---

## 1. Guideline Routing

> **Project is pre-configured via environment variable.**
> The target Taiga project is already set through an environment variable and is used as-is by the CLI.
> **Do NOT query, list, or confirm the project** — never run commands like `list-projects` or similar. Just proceed directly with the task.

> Authentication is handled automatically — the CLI reads the Taiga token directly from the Chrome browser session.

Choose the appropriate guideline based on the nature of the request:

| Request type              | Guideline                  |
|---------------------------|----------------------------|
| Client issue / bug report | `issue_guideline.md`       |
| Future work / TODO        | `future_task_guideline.md` |
| New feature / large task  | `feature_guideline.md`     |

Follow the title pattern and description template defined in the chosen guideline strictly.
Use Markdown formatting for readability.

---

## 2. Querying User Stories

### Search by name (`search-userstories`)

Use when you need to find a US by keyword.

```bash
taiga-cli search-userstories --query "<keyword>" --me
```

Output: `ID`, `Ref (#number)`, `Subject`, `Assignee`

- **1 result** → select it automatically and proceed.
- **2+ results** → ask the user to choose.

### Fetch by ID or Ref (`get-userstory`)

Use when you already know the exact internal ID or `#ref` number.

```bash
taiga-cli get-userstory --id <US_ID>
taiga-cli get-userstory --ref <REF>
```

Output: `ID`, `Ref (#number)`, `Subject`, `Assignee`, `Version`, `URL`

---

## 3. Creating & Updating

### Create a User Story

Always create a User Story as the primary unit of work.

```bash
taiga-cli create-userstory --subject "<SUBJECT>" --description "<DESCRIPTION>"
```

Add tasks only when needed:

```bash
# Simple list
taiga-cli create-userstory --subject "<SUBJECT>" --tasks "Task 1" "Task 2"

# With descriptions (recommended)
taiga-cli create-userstory --subject "<SUBJECT>" --tasks-json '[{"subject": "...", "description": "..."}]'
```

Add `--me` if the user says "assign to me" or "my task".

### Update a User Story

Resolve the internal ID first (see section 2), then update only the fields that need to change.

```bash
# By internal ID
taiga-cli update-userstory --id <US_ID> --subject "<new title>" --description "<new desc>" --me

# By ref number
taiga-cli update-userstory --ref <REF> --subject "<new title>" --me
```

Available fields: `--subject`, `--description`, `--status <STATUS_ID>`, `--assigned-to <USER_ID>`, `--me`

### Add Tasks to an Existing US

Use `create-task` only when adding tasks to an already-existing User Story.

```bash
# Resolve the US internal ID first, then:
taiga-cli create-task --us <US_ID> --tasks-json '[{"subject": "...", "description": "..."}, ...]'

# Or by ref
taiga-cli create-task --us-ref <US_REF> --tasks "Task 1" "Task 2"
```

---

## 4. Example Flows

| User request                                                                     | Action                                                                                               |
|----------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| "Client A has a payment error, here's the log — create a task."                  | Apply `issue_guideline.md` → `create-userstory`                                                      |
| "Add a TODO for API modularization refactoring."                                 | Apply `future_task_guideline.md` → `create-userstory`                                                |
| "Add dark mode support feature, split backend and frontend tasks, assign to me." | Apply `feature_guideline.md` → `create-userstory --tasks-json ... --me`                              |
| "Add one more task to the 'Login Improvement' user story."                       | `search-userstories --query "Login Improvement"` → `create-task --us <ID>`                           |
| "Add a task to US #42."                                                          | `get-userstory --ref 42` → `create-task --us <ID>`                                                   |
| "Rename 'Dark Mode Support' US to 'Dark Mode Support (v2)', assign to me."       | `search-userstories --query "Dark Mode Support"` → `update-userstory --id <ID> --subject "..." --me` |
| "Update the title of US #42."                                                    | `update-userstory --ref 42 --subject "<new title>"`                                                  |
