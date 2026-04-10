from modules.browser.api_client import AuthMode, BrowserTokenBaseClient
from modules.taiga.config import TaigaSettings, get_taiga_settings


class TaigaClient(BrowserTokenBaseClient):
    """HTTP client for interacting with the Taiga project management API.

    Inherits browser-session discovery and httpx client management from
    ``BrowserTokenBaseClient``.  Authenticates via a Bearer token stored
    in the browser's localStorage.

    Attributes:
        settings: Taiga connection settings (domain, project ID, etc.).
    """

    def __init__(self, settings: TaigaSettings | None = None):
        """Initialize TaigaClient with settings and discover auth token from browser session."""
        self.settings: TaigaSettings = settings or get_taiga_settings()
        self._project_id = self.settings.project_id
        self._me = None
        super().__init__()

    # ── BrowserTokenBaseClient configuration ────────────────────────────

    @property
    def domain(self) -> str:
        return self.settings.domain

    @property
    def auth_mode(self) -> AuthMode:
        return AuthMode.BEARER

    @property
    def local_storage_fields(self) -> list[str] | None:
        return ["token"]

    @property
    def base_url_suffix(self) -> str:
        return "/api/v1"

    # ── Helpers ─────────────────────────────────────────────────────────

    def _raise_for_status(self, response):
        """Raise httpx.HTTPStatusError for non-2xx responses (excluding auth codes handled by base)."""
        response.raise_for_status()

    @property
    def project_id(self):
        """Return the project ID, raising ValueError if not set."""
        if not self._project_id:
            raise ValueError("Project ID is not set. Please set it in the configuration.")
        return self._project_id

    def set_project_id(self, project_id):
        """Set the project ID for subsequent API calls."""
        self._project_id = project_id

    # ── API methods ─────────────────────────────────────────────────────

    def get_projects(self):
        """Fetch all projects accessible to the authenticated user."""
        response = self.get("/projects")
        self._raise_for_status(response)
        return response.json()

    def get_me(self):
        """Return the current authenticated user info, cached after first call."""
        if self._me is not None:
            return self._me
        response = self.get("/users/me")
        self._raise_for_status(response)
        self._me = response.json()
        return self._me

    def create_user_story(self, subject, description="", status=None, assigned_to=None):
        """Create a new user story in the current project.

        Args:
            subject: Title of the user story.
            description: Detailed description of the user story.
            status: Status ID to assign.
            assigned_to: User ID to assign the story to.

        Returns:
            The created user story as a dict.
        """
        data = {"project": self.project_id, "subject": subject, "description": description}
        if status:
            data["status"] = status
        if assigned_to:
            data["assigned_to"] = assigned_to

        response = self.post("/userstories", json=data)
        self._raise_for_status(response)
        return response.json()

    def search_user_stories(self, query=None, assigned_to_me=False):
        """Search user stories in the current project with optional filtering.

        Args:
            query: Case-insensitive substring to match against story subjects.
            assigned_to_me: If True, filter stories assigned to the current user.

        Returns:
            A list of matching user story dicts.
        """
        params = {"project": self.project_id}
        if assigned_to_me:
            me = self.get_me()
            params["assigned_to"] = me["id"]
        response = self.get("/userstories", params=params)
        self._raise_for_status(response)
        stories = response.json()
        if query:
            q = query.lower()
            stories = [s for s in stories if q in s["subject"].lower()]
        return stories

    def get_user_story(self, us_id):
        """Fetch a single user story by its ID."""
        response = self.get(f"/userstories/{us_id}")
        self._raise_for_status(response)
        return response.json()

    def get_user_story_by_ref(self, ref):
        """Fetch a single user story by its reference number within the project."""
        params = {"ref": ref, "project": self.project_id}
        response = self.get("/userstories/by_ref", params=params)
        self._raise_for_status(response)
        return response.json()

    def update_user_story(self, us_id, subject=None, description=None, status=None, assigned_to=None, version=None):
        """Update fields of an existing user story.

        Args:
            us_id: The user story ID to update.
            subject: New title for the user story.
            description: New description for the user story.
            status: New status ID.
            assigned_to: New assignee user ID.
            version: Optimistic locking version; fetched automatically if not provided.

        Returns:
            The updated user story as a dict.
        """
        if version is None:
            current = self.get_user_story(us_id)
            version = current["version"]

        data = {"version": version}
        if subject is not None:
            data["subject"] = subject
        if description is not None:
            data["description"] = description
        if status is not None:
            data["status"] = status
        if assigned_to is not None:
            data["assigned_to"] = assigned_to

        response = self.patch(f"/userstories/{us_id}", json=data)
        self._raise_for_status(response)
        return response.json()

    def get_userstory_custom_attributes(self):
        """Fetch all custom attribute definitions for user stories in the current project."""
        response = self.get("/userstory-custom-attributes", params={"project": self.project_id})
        self._raise_for_status(response)
        return response.json()

    def get_userstory_custom_attribute_values(self, us_id):
        """Fetch custom attribute values for a specific user story."""
        response = self.get(f"/userstories/custom-attributes-values/{us_id}")
        self._raise_for_status(response)
        return response.json()

    def update_userstory_custom_attribute_values(self, us_id, attributes_values: dict, version=None):
        """Update custom attribute values for a specific user story.

        Args:
            us_id: The user story ID whose custom attributes to update.
            attributes_values: Dict mapping custom attribute IDs to their new values.
            version: Optimistic locking version; fetched automatically if not provided.

        Returns:
            The updated custom attribute values as a dict.
        """
        if version is None:
            current = self.get_userstory_custom_attribute_values(us_id)
            version = current["version"]
        data = {
            "attributes_values": attributes_values,
            "version": version,
        }
        response = self.patch(f"/userstories/custom-attributes-values/{us_id}", json=data)
        self._raise_for_status(response)
        return response.json()

    def create_task(self, subject, description="", status=None, assigned_to=None, user_story=None):
        """Create a new task in the current project.

        Args:
            subject: Title of the task.
            description: Detailed description of the task.
            status: Status ID to assign.
            assigned_to: User ID to assign the task to.
            user_story: User story ID to associate the task with.

        Returns:
            The created task as a dict.
        """
        data = {"project": self.project_id, "subject": subject, "description": description}
        if status:
            data["status"] = status
        if assigned_to:
            data["assigned_to"] = assigned_to
        if user_story:
            data["user_story"] = user_story

        response = self.post("/tasks", json=data)
        self._raise_for_status(response)
        return response.json()
