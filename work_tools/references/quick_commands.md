# ⚡ Quick Commands Reference

AI-assisted workflows (recipes) for the `work-tools` skill. These commands are triggered by the `@work-tools <command>` pattern and involve multi-tool sequences.

---

## 1. `import-ims <url>` (Create US from IMS)

**Usage:** `@work-tools import-ims <ims-url>`
**Description:** Imports an IMS (Issue Management System) document and creates a structured Taiga User Story.

**Agent Recipe:**
1. **Fetch Data:** Call `wt ims get-document-from-url --url <url>` to retrieve the source document.
2. **Load Guidelines:** Call `wt docs read-docs task-writer` to load naming conventions and templates.
3. **Map & Create:**
    - Match the IMS content to the appropriate guideline (Issue/Feature/TODO).
    - Apply `wt taiga create-userstory` with mapped subjects, descriptions, and custom attributes.
    - If the user specifies "assign to me", include the `--me` flag.

---

## 2. `sync-context #ref` (Smart US Sync)

**Usage:** `@work-tools sync-context #<ref>`
**Description:** Refreshes the full context of a User Story and identifies if updates are needed.

**Agent Recipe:**
1. **Fetch Context:** Call `wt workflow get-context --ref <ref>` to get US, tasks, comments, and linked IMS docs.
2. **Analyze:** Check for new IMS comments, status changes in related documents, or pending tasks.
3. **Update:** Suggest or execute `wt taiga update-userstory` or `update-task` if any information has changed.

---

## 3. `sync-git #ref` (Git-to-Taiga Sync)

**Usage:** `@work-tools sync-git #<ref>`
**Description:** Analyzes the current Git branch or staged commits and updates the related User Story status or progress.

**Agent Recipe:**
1. **Fetch Git Info:** Call `wt git log --branch` or `wt git commit-info` to get the latest changes.
2. **Identify Story:** Confirm the User Story `#ref` matches the changes.
3. **Update:** Update the US description (e.g., ticking off checklists) or add a comment via `wt taiga update-userstory` to reflect development progress.

---

## 4. `gen-commit` (Commit Message Generator)

**Usage:** `@work-tools gen-commit`
**Description:** Analyzes staged changes and recent commit history to suggest a consistent, high-quality commit message.

**Agent Recipe:**
1. **Fetch Data:** Call `wt git commit-info` to gather staged diffs, logs, and style guides.
2. **Generate:** Propose a commit message following the **Conventional Commits** specification defined in `commit_style.md`.
3. **Refine:** Ask for user confirmation before proceeding with the commit.
