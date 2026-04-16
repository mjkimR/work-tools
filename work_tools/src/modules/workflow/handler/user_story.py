from modules.ims.client import ImsClient
from modules.taiga.client import TaigaClient


class UserStoryHandler:
    def __init__(self, taiga_client: TaigaClient, ims_client: ImsClient):
        self.taiga_client = taiga_client
        self.ims_client = ims_client

    def get_full_context(self, user_story_ref: str):
        """Fetch a user story by reference and print its full context, including linked tasks and comments.

        - Fetch the user story using the Taiga API.
        - Fetch custom attributes and their values for the user story.
        - Fetch linked tasks and comments.
        - Fetch related IMS documents if external references are found in the description or custom attributes.
        - Print all information in a structured format for easy reading.
        """
        taiga = self.taiga_client
        ims = self.ims_client

        # ── 1. User Story ────────────────────────────────────────────────
        us = taiga.get_user_story_by_ref(int(user_story_ref))
        us_id = us["id"]
        project_slug = us["project_extra_info"]["slug"]
        assigned = us.get("assigned_to_extra_info")
        assignee = assigned["full_name_display"] if assigned else "Unassigned"

        print("=" * 60)
        print(f"[User Story] #{us['ref']} - {us['subject']}")
        print(f"  Status   : {us['status_extra_info']['name']}")
        print(f"  Assignee : {assignee}")
        print(f"  URL      : https://tree.taiga.io/project/{project_slug}/us/{us['ref']}")
        print()
        desc = us.get("description") or "(none)"
        indented_desc = "\n".join(f"    {line}" for line in desc.splitlines())
        print(f"  Description:\n{indented_desc}")
        print()

        # ── 2. Custom Attributes ─────────────────────────────────────────
        attr_defs = taiga.get_userstory_custom_attributes()
        attr_map = {str(a["id"]): a["name"] for a in attr_defs}
        ca_result = taiga.get_userstory_custom_attribute_values(us_id)
        ca_values = ca_result.get("attributes_values", {})

        print("[Custom Attributes]")
        if ca_values:
            for attr_id, value in ca_values.items():
                name = attr_map.get(str(attr_id), f"ID:{attr_id}")
                print(f"  {name}: {value}")
        else:
            print("  (none)")
        print()

        # ── 3. Linked Tasks ──────────────────────────────────────────────
        tasks = taiga.get_tasks_by_userstory(us_id)
        print(f"[Tasks] ({len(tasks)} total)")
        for task in tasks:
            t_assigned = task.get("assigned_to_extra_info")
            t_assignee = t_assigned["full_name_display"] if t_assigned else "Unassigned"
            t_status = task.get("status_extra_info", {}).get("name", "")
            print(f"  - #{task['ref']} [{t_status}] {task['subject']} (Assignee: {t_assignee})")
            print(f"    URL: https://tree.taiga.io/project/{project_slug}/task/{task['ref']}")
        if not tasks:
            print("  (none)")
        print()

        # ── 4. Comments ──────────────────────────────────────────────────
        comments = taiga.get_userstory_comments(us_id)
        print(f"[Comments] ({len(comments)} total)")
        for c in comments:
            user = c.get("user", {}).get("name", "Unknown")
            created_raw = c.get("created_at", "")
            created = created_raw[:16].replace("T", " ") if created_raw else ""
            comment_text = c.get("comment", "")
            indented_comment = "\n".join(f"    {line}" for line in comment_text.splitlines())
            print(f"  [{created}] {user}:")
            print(indented_comment)
        if not comments:
            print("  (none)")
        print()

        # ── 5. Linked IMS Documents ──────────────────────────────────────
        util = ims.util
        texts: list[str] = []
        if us.get("description"):
            texts.append(us["description"])
        for v in ca_values.values():
            if isinstance(v, str):
                texts.append(v)

        seen: set[str] = set()
        uuids: list[str] = []
        for text in texts:
            for url in util.get_ims_url(text):
                uuid = util.parse_uuid_from_url(url)
                if uuid and uuid not in seen:
                    seen.add(uuid)
                    uuids.append(uuid)

        print(f"[IMS Documents] ({len(uuids)} linked)")
        if uuids:
            docs = ims.get_documents(uuids)
            for doc in docs:
                print(str(doc))
                print()
        else:
            print("  (none)")
        print("=" * 60)
