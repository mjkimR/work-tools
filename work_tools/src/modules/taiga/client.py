import requests
from modules.browser.session import get_session_info
from modules.taiga.config import TaigaSettings, get_taiga_settings


class TaigaClient:
    def __init__(self, settings: TaigaSettings | None = None):
        self.settings: TaigaSettings = settings or get_taiga_settings()

        discovered_token, discovered_url = get_session_info(self.settings.domain)
        self.token = discovered_token
        self.base_url = discovered_url
        self._project_id = self.settings.project_id
        self._me = None

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    @property
    def project_id(self):
        if not self._project_id:
            raise ValueError("Project ID is not set. Please set it in the configuration.")
        return self._project_id

    def set_project_id(self, project_id):
        self._project_id = project_id

    def get_projects(self):
        url = f"{self.base_url}/projects"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_me(self):
        if self._me is not None:
            return self._me
        url = f"{self.base_url}/users/me"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        self._me = response.json()
        return self._me

    def create_user_story(self, subject, description="", status=None, assigned_to=None):
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
        url = f"{self.base_url}/userstories/{us_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_user_story_by_ref(self, ref):
        url = f"{self.base_url}/userstories/by_ref"
        params = {"ref": ref, "project": self.project_id}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def update_user_story(self, us_id, subject=None, description=None, status=None, assigned_to=None, version=None):
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
        url = f"{self.base_url}/userstory-custom-attributes"
        response = requests.get(url, headers=self.headers, params={"project": self.project_id})
        response.raise_for_status()
        return response.json()

    def get_userstory_custom_attribute_values(self, us_id):
        url = f"{self.base_url}/userstories/custom-attributes-values/{us_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def update_userstory_custom_attribute_values(self, us_id, attributes_values: dict, version=None):
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
