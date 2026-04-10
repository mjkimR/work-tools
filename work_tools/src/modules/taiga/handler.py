import json

from modules.taiga.client import TaigaClient


class TaigaCLIHandlers:
    """CLI command handlers that bridge Click commands to TaigaClient API calls.

    Each public method corresponds to a CLI subcommand and handles
    argument resolution, API interaction, and output formatting.
    """

    def __init__(self):
        """Initialize handlers with a TaigaClient instance."""
        self.client = TaigaClient()

    # ── Common Helpers ───────────────────────────────────────────────────────

    def _resolve_us_id(
        self,
        id=None,
        ref=None,
    ) -> int:
        """Resolve a user story's internal ID from either an ID or a ref number."""
        if id is not None:
            return id
        if ref is None:
            raise ValueError("Either id or ref must be provided")
        resolved = self.client.get_user_story_by_ref(ref)
        print(f"Ref #{ref} → Internal ID: {resolved['id']} ({resolved['subject']})")
        return resolved["id"]

    def _resolve_assigned_to(self, me=False, assigned_to=None, label="Assigning to") -> int | None:
        """Resolve the assignee user ID, using the current user if `me` is True."""
        if me:
            user = self.client.get_me()
            print(f"{label}: {user['full_name']} (ID: {user['id']})")
            return user["id"]
        return assigned_to

    # ── Command Handlers ──────────────────────────────────────────────────────

    def list_projects(self):
        """List all accessible projects."""
        projects = self.client.get_projects()
        for p in projects:
            print(f"ID: {p['id']} | Name: {p['name']} | Slug: {p['slug']}")

    def search_userstories(self, query=None, me=False):
        """Search user stories with optional query and assignee filter."""
        stories = self.client.search_user_stories(query=query, assigned_to_me=me)
        if not stories:
            print("No results found.")
            return
        for s in stories:
            assigned = s.get("assigned_to_extra_info")
            assignee = assigned["full_name_display"] if assigned else "Unassigned"
            print(f"ID: {s['id']} | Ref: #{s['ref']} | Subject: {s['subject']} | Assignee: {assignee}")

    def get_userstory(self, id=None, ref=None):
        """Fetch and display a single user story by ID or ref."""
        us_id = self._resolve_us_id(id=id, ref=ref)
        us = self.client.get_user_story(us_id)
        print(f"ID: {us['id']} | Ref: #{us['ref']} | Subject: {us['subject']}")
        assigned = us.get("assigned_to_extra_info")
        print(f"Assignee: {assigned['full_name_display'] if assigned else 'Unassigned'}")
        print(f"Version: {us['version']}")
        print(f"URL: https://tree.taiga.io/project/{us['project_extra_info']['slug']}/us/{us['ref']}")

    def update_userstory(
        self, id=None, ref=None, project=None, subject=None, description=None, status=None, me=False, assigned_to=None
    ):
        """Update an existing user story's fields."""
        us_id = self._resolve_us_id(id=id, ref=ref)
        resolved_assigned = self._resolve_assigned_to(me=me, assigned_to=assigned_to)
        us = self.client.update_user_story(
            us_id,
            subject=subject,
            description=description,
            status=status,
            assigned_to=resolved_assigned,
        )
        print(f"User Story updated: {us['id']} - {us['subject']}")
        print(f"US URL: https://tree.taiga.io/project/{us['project_extra_info']['slug']}/us/{us['ref']}")

    def create_userstory(self, subject, description="", tasks=None, tasks_json=None, me=False):
        """Create a new user story, optionally with associated tasks."""
        assigned_to = self._resolve_assigned_to(me=me)
        us = self.client.create_user_story(subject, description, assigned_to=assigned_to)
        print(f"User Story created: {us['id']} - {us['subject']}")
        print(f"US URL: https://tree.taiga.io/project/{us['project_extra_info']['slug']}/us/{us['ref']}")

        tasks_to_create = []
        if tasks_json:
            try:
                tasks_to_create = json.loads(tasks_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"Error parsing --tasks-json: {e}") from e
        elif tasks:
            tasks_to_create = [{"subject": t, "description": ""} for t in tasks]

        for task_data in tasks_to_create:
            task = self.client.create_task(
                task_data["subject"],
                description=task_data.get("description", ""),
                user_story=us["id"],
                assigned_to=assigned_to,
            )
            print(f"  - Task created: {task['id']} - {task['subject']}")

    def create_task(self, subject=None, description="", tasks=None, tasks_json=None, us=None, us_ref=None, me=False):
        """Create one or more tasks, optionally linked to a user story."""
        assigned_to = self._resolve_assigned_to(me=me, label="Assigning task(s) to")

        us_id = None
        if us is not None or us_ref is not None:
            us_id = self._resolve_us_id(id=us, ref=us_ref)

        tasks_to_create = []
        if tasks_json:
            try:
                tasks_to_create = json.loads(tasks_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"Error parsing --tasks-json: {e}") from e
        elif tasks:
            tasks_to_create = [{"subject": t, "description": ""} for t in tasks]
        elif subject:
            tasks_to_create = [{"subject": subject, "description": description}]
        else:
            raise ValueError("At least one of --subject, --tasks, or --tasks-json must be provided")

        for task_data in tasks_to_create:
            task = self.client.create_task(
                task_data["subject"],
                description=task_data.get("description", ""),
                assigned_to=assigned_to,
                user_story=us_id,
            )
            print(f"Task created: {task['id']} - {task['subject']}")
            if task.get("user_story"):
                print(f"  Linked to US ID: {task['user_story']}")
            print(f"  URL: https://tree.taiga.io/project/{task['project_extra_info']['slug']}/task/{task['ref']}")

    def list_custom_attributes(self):
        """List all custom attribute definitions for user stories."""
        attrs = self.client.get_userstory_custom_attributes()
        if not attrs:
            print("No custom attributes found.")
        else:
            for attr in attrs:
                env_key = "TAIGA_CA_" + attr["name"].upper().replace(" ", "_").replace("-", "_")
                print(f"ID: {attr['id']} | Name: {attr['name']} | Type: {attr['type']} | Env: {env_key}")

    def get_custom_attr_values(self, id=None, ref=None):
        """Fetch and display custom attribute values for a user story."""
        us_id = self._resolve_us_id(id=id, ref=ref)
        attr_map = {}
        for attr in self.client.get_userstory_custom_attributes():
            attr_map[str(attr["id"])] = attr["name"]
        result = self.client.get_userstory_custom_attribute_values(us_id)
        values = result.get("attributes_values", {})
        if not values:
            print("No custom attribute values set.")
        else:
            for attr_id, value in values.items():
                name = attr_map.get(str(attr_id), f"ID:{attr_id}")
                print(f"  {name} (ID: {attr_id}): {value}")

    def update_custom_attr_values(self, values_json, id=None, ref=None):
        """Update custom attribute values for a user story from a JSON string."""
        us_id = self._resolve_us_id(id=id, ref=ref)
        try:
            values_dict = json.loads(values_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing --values-json: {e}") from e
        result = self.client.update_userstory_custom_attribute_values(us_id, values_dict)
        print(f"Custom attribute values updated for US ID: {us_id}")
        for attr_id, value in result.get("attributes_values", {}).items():
            print(f"  ID {attr_id}: {value}")
