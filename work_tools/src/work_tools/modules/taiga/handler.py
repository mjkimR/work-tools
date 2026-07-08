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

    def _build_custom_attrs_dict(self, custom_attrs) -> dict:
        """Parse 'attr_id::value' pairs into a dict, validating dropdown values.

        For ``dropdown`` custom attributes, Taiga stores the selected option text
        as-is, so the value must exactly match one of the options defined in the
        attribute's ``extra`` list. Any mismatch raises ``ValueError`` before the
        story is created/updated, preventing silently-invalid values from being saved.

        Args:
            custom_attrs: Iterable of 'attr_id::value' strings.

        Returns:
            Dict mapping attribute ID (str) to its value.

        Raises:
            ValueError: If a dropdown value is not among its allowed options.
        """
        attrs_dict = {}
        for attr_str in custom_attrs:
            if "::" not in attr_str:
                continue
            attr_id, attr_val = attr_str.split("::", 1)
            attrs_dict[attr_id.strip()] = attr_val

        if not attrs_dict:
            return attrs_dict

        # Only fetch definitions when needed, to validate dropdown selections.
        attr_defs = {str(a["id"]): a for a in self.client.get_userstory_custom_attributes()}
        for attr_id, value in attrs_dict.items():
            definition = attr_defs.get(str(attr_id))
            if not definition or definition.get("type") != "dropdown":
                continue
            options = definition.get("extra") or []
            if value not in options:
                name = definition.get("name", f"ID:{attr_id}")
                allowed = ", ".join(options) if options else "(no options defined)"
                raise ValueError(
                    f"'{value}' is not a valid option for '{name}' (ID:{attr_id}). "
                    f"Choose one of: {allowed}"
                )

        return attrs_dict

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

        # Validate custom attributes up front so an invalid value fails before
        # anything is created (no orphaned User Story on a bad dropdown value).
        attrs_dict = self._build_custom_attrs_dict(custom_attrs) if custom_attrs else None

        # 1. Create Core User Story
        us = self.client.create_user_story(
            subject=subject, description=description, status=status, assigned_to=resolved_assignee
        )
        us_id = us["id"]
        print(f"✅ User Story created: #{us['ref']} - {us['subject']}")
        print(f"   URL: https://tree.taiga.io/project/{us['project_extra_info']['slug']}/us/{us['ref']}")

        # 2. Update Custom Attributes if provided
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
        self,
        ref,
        subject=None,
        description=None,
        status=None,
        custom_attrs=None,
        comment=None,
        me=False,
        assigned_to=None,
    ):
        """Unified update: Core US fields and Custom Attributes via #ref"""
        us_id = self._get_id_from_ref(ref)
        resolved_assignee = self._resolve_assigned_to(me=me, assigned_to=assigned_to)

        # Validate custom attributes up front so an invalid value fails before
        # any core field is mutated (all-or-nothing on a bad dropdown value).
        attrs_dict = self._build_custom_attrs_dict(custom_attrs) if custom_attrs else None

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
