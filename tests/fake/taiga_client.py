"""FakeTaigaClient — drop-in replacement for TaigaClient without browser/HTTP.

Matches TaigaClient's public method signatures exactly.
If a signature changes, tests using this fake will break → interface drift detected.
"""

from tests.fake.data.taiga import (
    COMMENTS,
    CUSTOM_ATTRIBUTE_VALUES,
    CUSTOM_ATTRIBUTES,
    ME,
    PROJECTS,
    TASKS,
    USER_STORIES,
    USER_STORY_BY_REF,
    make_task,
)


class FakeTaigaClient:
    """Fake that replaces TaigaClient for handler-level testing."""

    def __init__(self):
        self._project_id = 1
        self._me = ME

        # Call recordings for assertions
        self.created_stories: list[dict] = []
        self.created_tasks: list[dict] = []
        self.updated_stories: list[dict] = []
        self.updated_ca_values: list[dict] = []

    # ── Properties matching TaigaClient ──────────────────────────────────

    @property
    def project_id(self):
        if not self._project_id:
            raise ValueError("Project ID is not set.")
        return self._project_id

    def set_project_id(self, project_id):
        self._project_id = project_id

    # ── API methods (same signatures as TaigaClient) ─────────────────────

    def get_projects(self):
        return PROJECTS

    def get_me(self):
        return self._me

    def create_user_story(self, subject, description="", status=None, assigned_to=None):
        story = {
            "id": 200 + len(self.created_stories),
            "ref": 80 + len(self.created_stories),
            "project": self._project_id,
            "subject": subject,
            "description": description,
            "status": status,
            "assigned_to": assigned_to,
            "version": 1,
            "assigned_to_extra_info": {"full_name_display": "Test User"} if assigned_to else None,
            "project_extra_info": {"slug": "test-project"},
        }
        self.created_stories.append(story)
        return story

    def search_user_stories(self, query=None, assigned_to_me=False):
        stories = list(USER_STORIES.values())
        if assigned_to_me:
            pass  # In fake, return all — handler logic is what we test
        if query:
            q = query.lower()
            stories = [s for s in stories if q in s["subject"].lower()]
        return stories

    def get_user_story(self, us_id):
        if us_id in USER_STORIES:
            return USER_STORIES[us_id]
        raise ValueError(f"User story {us_id} not found in fake data")

    def get_user_story_by_ref(self, ref):
        if ref in USER_STORY_BY_REF:
            return USER_STORY_BY_REF[ref]
        raise ValueError(f"User story ref #{ref} not found in fake data")

    def update_user_story(self, us_id, subject=None, description=None, status=None, assigned_to=None, comment=None, version=None):
        base = self.get_user_story(us_id).copy()
        if subject is not None:
            base["subject"] = subject
        if description is not None:
            base["description"] = description
        if status is not None:
            base["status"] = status
        if assigned_to is not None:
            base["assigned_to"] = assigned_to
        base["version"] = (version or base["version"]) + 1
        self.updated_stories.append(base)
        return base

    def get_userstory_custom_attributes(self):
        return CUSTOM_ATTRIBUTES

    def get_userstory_custom_attribute_values(self, us_id):
        return CUSTOM_ATTRIBUTE_VALUES.get(us_id, {"version": 1, "attributes_values": {}})

    def update_userstory_custom_attribute_values(self, us_id, attributes_values: dict, version=None):
        result = {
            "version": (version or 1) + 1,
            "attributes_values": attributes_values,
        }
        self.updated_ca_values.append({"us_id": us_id, **result})
        return result

    def create_task(self, subject, description="", status=None, assigned_to=None, user_story=None):
        task = make_task(subject, description, assigned_to, user_story)
        self.created_tasks.append(task)
        return task

    def get_tasks_by_userstory(self, us_id):
        return TASKS.get(us_id, [])

    def get_userstory_comments(self, us_id):
        return COMMENTS.get(us_id, [])
