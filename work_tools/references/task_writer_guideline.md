# Task Writer Guideline

Detailed instructions for managing Taiga user stories and tasks via CLI.

---

## 1. Guideline Routing

> **Project is pre-configured via environment variable.**
> The target Taiga project is already set through an environment variable and is used as-is by the CLI.
> **Do NOT query, list, or confirm the project** — never run commands like `list-projects` or similar. Just proceed
> directly with the task.

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

## 2. Querying Context

### Get Full Context of a User Story (`wt workflow`)

Use when you need to view the full details of a User Story, including its linked tasks, comments, custom attributes, and
related IMS documents.

```bash
wt workflow get-context --ref <US_REF>
```

---

## 3. Creating & Updating

> **🚨 IMPORTANT: Do NOT set or update the `status` field.**
> Status management is strictly handled manually by human users. Never use the `--status` option in any of your commands.

> **🚨 IMPORTANT: Do NOT use GFM checkboxes (`[ ]` or `[x]`).**
> Taiga does not support GFM checkbox syntax in descriptions, and it will break the formatting. 
> Use standard bullet points (`-` or `*`).

### Create a User Story
Always create a User Story as the primary unit of work. You can create the story, attach tasks, and set custom attributes **in one go**.

```bash
# Basic creation
wt taiga create-userstory --subject "<SUBJECT>" --description "<DESCRIPTION>"

# With tasks and custom attributes
wt taiga create-userstory \
  --subject "<SUBJECT>" \
  --tasks "Task 1::Detailed description" \
  --tasks "Task 2::Another description" \
  --custom-attrs "123::Value A" \
  --custom-attrs "456::Value B" \
  --me
```
*Note: Use `::` to separate subject and description in the `--tasks` option, and `ID::Value` for `--custom-attrs`. Always repeat the flag for multiple items (e.g., `--tasks "A" --tasks "B"`).*
*Add `--me` if the user says "assign to me" or "my task".*

### Update a User Story
Update an existing User Story's core fields and/or custom attributes directly using its `#ref` number.

```bash
# Update subject and assign to me
wt taiga update-userstory --ref <US_REF> --subject "<new title>" --me

# Update description and custom attributes
wt taiga update-userstory --ref <US_REF> --description "<new desc>" --custom-attrs "123::new value"
```
*Available fields:* `--subject`, `--description`, `--custom-attrs`, `--assigned-to <USER_ID>`, `--me`

### Add Tasks to an Existing US
Use `create-task` only when adding new tasks to an **already-existing** User Story.

```bash
# By using the US ref number
wt taiga create-task --us-ref <US_REF> --tasks "Task 1" --tasks "Task 2"

# With descriptions using :: delimiter (recommended for AI agents)
wt taiga create-task --us-ref <US_REF> --tasks "Task 1::Description here" --tasks "Task 2::Another description"
```

### Update a Task
Update an existing Task directly using its `#ref` number. 

```bash
# Assign to me
wt taiga update-task --ref <TASK_REF> --me

# Change subject
wt taiga update-task --ref <TASK_REF> --subject "<new task title>"
```

---

## 4. Example Flows

| User request                                                                     | Action                                                                                 |
|----------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| "Client A has a payment error, here's the log — create a task."                  | Apply `issue_guideline.md` → `wt taiga create-userstory ...`                          |
| "Add a TODO for API modularization refactoring."                                 | Apply `future_task_guideline.md` → `wt taiga create-userstory ...`                    |
| "Add dark mode support feature, split backend and frontend tasks, assign to me." | Apply `feature_guideline.md` → `wt taiga create-userstory --tasks-json ... --me`      |
| "Add one more task to US #42."                                                   | `wt taiga create-task --us-ref 42 --subject "..."`                                    |
| "Update the title and custom attributes of US #42."                              | `wt taiga update-userstory --ref 42 --subject "..." --custom-attrs "1::v"`           |
| "Reassign Task #105 to me and update its status."                                | `wt taiga update-task --ref 105 --status <ID> --me`                                   |
| "Check what tasks are left in US #42."                                           | `wt workflow get-context --ref 42`                                                    |
