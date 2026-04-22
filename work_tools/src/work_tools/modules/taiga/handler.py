import json

from work_tools.modules.taiga.client import TaigaClient


class TaigaCLIHandlers:
    def __init__(self):
        self.client = TaigaClient()

    # ── Internal Helpers ─────────────────────────────────────────────────────
    def _get_id_from_ref(self, ref: int) -> int:
        """Resolve a user story's internal ID exclusively from a ref number."""
        resolved = self.client.get_user_story_by_ref(ref)
        return resolved["id"]

    def _resolve_assigned_to(self, me=False, assigned_to=None, label="Assigning to") -> int | None:
        if me:
            user = self.client.get_me()
            print(f"{label}: {user['full_name']} (ID: {user['id']})")
            return user["id"]
        return assigned_to

    # ── Command Handlers ──────────────────────────────────────────────────────

    def create_userstory(
        self,
        subject,
        description="",
        status=None,
        tasks=None,
        tasks_json=None,
        custom_attrs=None,
        me=False,
        assigned_to=None,
    ):
        """Unified creation: Core US + Custom Attributes + Tasks"""
        resolved_assignee = self._resolve_assigned_to(me=me, assigned_to=assigned_to)

        # 1. Create Core User Story
        us = self.client.create_user_story(
            subject=subject, description=description, status=status, assigned_to=resolved_assignee
        )
        us_id = us["id"]
        print(f"✅ User Story created: #{us['ref']} - {us['subject']}")
        print(f"   URL: https://tree.taiga.io/project/{us['project_extra_info']['slug']}/us/{us['ref']}")

        # 2. Update Custom Attributes if provided
        if custom_attrs:
            attrs_dict = {}
            for attr_str in custom_attrs:
                if "::" in attr_str:
                    attr_id, attr_val = attr_str.split("::", 1)
                    attrs_dict[attr_id] = attr_val
            if attrs_dict:
                self.client.update_userstory_custom_attribute_values(us_id, attrs_dict)
                print("   Custom attributes applied.")

        # 3. Create Tasks if provided
        tasks_to_create = []
        if tasks_json:
            try:
                tasks_to_create = json.loads(tasks_json)
            except json.JSONDecodeError as e:
                print(f"⚠️ Failed to parse tasks_json: {e}")
        elif tasks:
            for t in tasks:
                if "::" in t:
                    subj, desc = t.split("::", 1)
                    tasks_to_create.append({"subject": subj, "description": desc})
                else:
                    tasks_to_create.append({"subject": t, "description": ""})

        for task_data in tasks_to_create:
            task = self.client.create_task(
                subject=task_data["subject"],
                description=task_data.get("description", ""),
                user_story=us_id,
                assigned_to=resolved_assignee,
            )
            print(f"   ↳ Task created: #{task['ref']} - {task['subject']}")

    def update_userstory(
        self, ref, subject=None, description=None, status=None, custom_attrs=None, comment=None, me=False, assigned_to=None
    ):
        """Unified update: Core US fields and Custom Attributes via #ref"""
        us_id = self._get_id_from_ref(ref)
        resolved_assignee = self._resolve_assigned_to(me=me, assigned_to=assigned_to)

        # 1. Update Core Fields (only if at least one field is provided)
        if any(v is not None for v in [subject, description, status, resolved_assignee, comment]):
            us = self.client.update_user_story(
                us_id,
                subject=subject,
                description=description,
                status=status,
                assigned_to=resolved_assignee,
                comment=comment,
            )
            print(f"✅ User Story #{us['ref']} updated.")

        # 2. Update Custom Attributes
        if custom_attrs:
            attrs_dict = {}
            for attr_str in custom_attrs:
                if "::" in attr_str:
                    attr_id, attr_val = attr_str.split("::", 1)
                    attrs_dict[attr_id] = attr_val
            if attrs_dict:
                self.client.update_userstory_custom_attribute_values(us_id, attrs_dict)
                print(f"   Custom attributes updated for #{ref}.")

    def create_task(self, us_ref, subject=None, description="", tasks=None, tasks_json=None, me=False):
        """Create tasks linked to a US via #ref"""
        us_id = self._get_id_from_ref(us_ref)
        resolved_assignee = self._resolve_assigned_to(me=me, label="Assigning task(s) to")

        tasks_to_create = []
        if tasks_json:
            try:
                tasks_to_create = json.loads(tasks_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"Error parsing tasks_json: {e}") from e
        elif tasks:
            for t in tasks:
                if "::" in t:
                    subj, desc = t.split("::", 1)
                    tasks_to_create.append({"subject": subj, "description": desc})
                else:
                    tasks_to_create.append({"subject": t, "description": ""})
        elif subject:
            tasks_to_create = [{"subject": subject, "description": description}]
        else:
            raise ValueError("At least one of --subject, --tasks, or --tasks-json must be provided")

        for task_data in tasks_to_create:
            task = self.client.create_task(
                subject=task_data["subject"],
                description=task_data.get("description", ""),
                assigned_to=resolved_assignee,
                user_story=us_id,
            )
            print(f"✅ Task created: #{task['ref']} - {task['subject']} (Linked to US #{us_ref})")

    # ── Internal Helpers ────────────────────────────────────────────────

    def _get_task_id_from_ref(self, ref: int) -> int:
        """Resolve a task's internal ID exclusively from a ref number."""
        resolved = self.client.get_task_by_ref(ref)
        return resolved["id"]

    # ── Command Handlers ───────────────────────────────────────────────

    def update_task(self, ref, subject=None, description=None, status=None, comment=None, me=False, assigned_to=None):
        """Update an existing Task's fields via #ref"""
        task_id = self._get_task_id_from_ref(ref)
        resolved_assignee = self._resolve_assigned_to(me=me, assigned_to=assigned_to)

        if any(v is not None for v in [subject, description, status, resolved_assignee, comment]):
            task = self.client.update_task(
                task_id=task_id,
                subject=subject,
                description=description,
                status=status,
                assigned_to=resolved_assignee,
                comment=comment,
            )
            print(f"✅ Task #{task['ref']} updated: {task['subject']}")
            print(f"   URL: https://tree.taiga.io/project/{task['project_extra_info']['slug']}/task/{task['ref']}")
        else:
            print("⚠️ No fields provided to update.")
