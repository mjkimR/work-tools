"""Hardcoded response data for FakeTaigaClient.

Mirrors the JSON structures returned by the real Taiga REST API so that
handler tests can run without any network access.
"""

ME = {
    "id": 10,
    "username": "testuser",
    "full_name": "Test User",
    "email": "test@example.com",
}

PROJECT = {
    "id": 1,
    "name": "Test Project",
    "slug": "test-project",
}

PROJECTS = [
    PROJECT,
    {"id": 2, "name": "Other Project", "slug": "other-project"},
]

_US_TEMPLATE = {
    "project": 1,
    "version": 1,
    "assigned_to_extra_info": {"full_name_display": "Test User"},
    "project_extra_info": {"slug": "test-project"},
}


def _make_us(us_id: int, ref: int, subject: str, **overrides) -> dict:
    return {**_US_TEMPLATE, "id": us_id, "ref": ref, "subject": subject, **overrides}


USER_STORIES = {
    100: _make_us(100, 42, "Implement login feature"),
    101: _make_us(101, 43, "Fix dashboard bug"),
    102: _make_us(102, 44, "Add search functionality"),
}

# ref → id lookup
USER_STORY_BY_REF = {us["ref"]: us for us in USER_STORIES.values()}

_TASK_TEMPLATE = {
    "project": 1,
    "project_extra_info": {"slug": "test-project"},
}

CUSTOM_ATTRIBUTES = [
    {"id": 1, "name": "Priority", "type": "text"},
    {"id": 2, "name": "Sprint-Goal", "type": "text"},
]

CUSTOM_ATTRIBUTE_VALUES = {
    100: {"version": 1, "attributes_values": {"1": "High", "2": "Complete login flow"}},
}

_task_id_seq = 500


def make_task(subject: str, description: str = "", assigned_to=None, user_story=None) -> dict:
    global _task_id_seq
    _task_id_seq += 1
    return {
        **_TASK_TEMPLATE,
        "id": _task_id_seq,
        "ref": _task_id_seq,
        "subject": subject,
        "description": description,
        "assigned_to": assigned_to,
        "user_story": user_story,
    }
