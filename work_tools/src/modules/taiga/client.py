import requests
from modules.browser.session import get_session_info
from modules.taiga.config import TaigaSettings, get_taiga_settings


class TaigaClient:
    """HTTP client for interacting with the Taiga project management API.

    Handles authentication via browser session discovery and provides methods
    for managing projects, user stories, tasks, and custom attributes.

    Attributes:
        settings: Taiga connection settings (domain, project ID, etc.).
        token: Bearer token discovered from the browser session.
        base_url: Base URL for the Taiga API.
        headers: Default HTTP headers including authorization.
    """

    def __init__(self, settings: TaigaSettings | None = None):
        """Initialize TaigaClient with settings and discover auth token from browser session."""
        self.settings: TaigaSettings = settings or get_taiga_settings()

        info = get_session_info(self.settings.domain, local_storage_fields=["token"])
        self.token = info.local_storage["token"]
        self.base_url = f"{info.base_url}/api/v1"
        self._project_id = self.settings.project_id
        self._me = None

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    @property
    def project_id(self):
        """Return the project ID, raising ValueError if not set."""
        if not self._project_id:
            raise ValueError("Project ID is not set. Please set it in the configuration.")
        return self._project_id

    def set_project_id(self, project_id):
        """Set the project ID for subsequent API calls."""
        self._project_id = project_id

    def get_projects(self):
        """Fetch all projects accessible to the authenticated user."""
        url = f"{self.base_url}/projects"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_me(self):
        """Return the current authenticated user info, cached after first call."""
        if self._me is not None:
            return self._me
        url = f"{self.base_url}/users/me"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
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
        url = f"{self.base_url}/userstories"
        data = {"project": self.project_id, "subject": subject, "description": description}
        if status:
            data["status"] = status
        if assigned_to:
            data["assigned_to"] = assigned_to

        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def search_user_stories(self, query=None, assigned_to_me=False):
        """Search user stories in the current project with optional filtering.

        Args:
            query: Case-insensitive substring to match against story subjects.
            assigned_to_me: If True, filter stories assigned to the current user.

        Returns:
            A list of matching user story dicts.
        """
        url = f"{self.base_url}/userstories"
        params = {"project": self.project_id}
        if assigned_to_me:
            me = self.get_me()
            params["assigned_to"] = me["id"]
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        stories = response.json()
        if query:
            q = query.lower()
            stories = [s for s in stories if q in s["subject"].lower()]
        return stories

    def get_user_story(self, us_id):
        """Fetch a single user story by its ID."""
        url = f"{self.base_url}/userstories/{us_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_user_story_by_ref(self, ref):
        """Fetch a single user story by its reference number within the project."""
        url = f"{self.base_url}/userstories/by_ref"
        params = {"ref": ref, "project": self.project_id}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
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

        url = f"{self.base_url}/userstories/{us_id}"
        data = {"version": version}
        if subject is not None:
            data["subject"] = subject
        if description is not None:
            data["description"] = description
        if status is not None:
            data["status"] = status
        if assigned_to is not None:
            data["assigned_to"] = assigned_to

        response = requests.patch(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def get_userstory_custom_attributes(self):
        """Fetch all custom attribute definitions for user stories in the current project."""
        url = f"{self.base_url}/userstory-custom-attributes"
        response = requests.get(url, headers=self.headers, params={"project": self.project_id})
        response.raise_for_status()
        return response.json()

    def get_userstory_custom_attribute_values(self, us_id):
        """Fetch custom attribute values for a specific user story."""
        url = f"{self.base_url}/userstories/custom-attributes-values/{us_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
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
        url = f"{self.base_url}/userstories/custom-attributes-values/{us_id}"
        data = {
            "attributes_values": attributes_values,
            "version": version,
        }
        response = requests.patch(url, headers=self.headers, json=data)
        response.raise_for_status()
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
        url = f"{self.base_url}/tasks"
        data = {"project": self.project_id, "subject": subject, "description": description}
        if status:
            data["status"] = status
        if assigned_to:
            data["assigned_to"] = assigned_to
        if user_story:
            data["user_story"] = user_story

        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
