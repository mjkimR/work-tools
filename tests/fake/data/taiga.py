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
    "status_extra_info": {"name": "New"},
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

# IMS 연동 테스트용 데이터
IMS_FAKE_BASE_URL = "https://ims.example.com"
IMS_UUID_IN_DESCRIPTION = "aaaa-1111-bbbb-2222"
IMS_UUID_IN_CUSTOM_ATTR = "cccc-3333-dddd-4444"

USER_STORIES_WITH_IMS = {
    # description에 IMS URL 포함
    200: {
        **_US_TEMPLATE,
        "id": 200,
        "ref": 50,
        "subject": "US with IMS link in description",
        "description": f"관련 요구사항: {IMS_FAKE_BASE_URL}/support-ai/?uid=8226&uuid={IMS_UUID_IN_DESCRIPTION}",
    },
    # custom attribute에 IMS URL 포함
    201: {
        **_US_TEMPLATE,
        "id": 201,
        "ref": 51,
        "subject": "US with IMS link in custom attr",
        "description": "설명 없음",
    },
    # IMS URL 없음
    202: {
        **_US_TEMPLATE,
        "id": 202,
        "ref": 52,
        "subject": "US with no IMS link",
        "description": "IMS 링크 없는 유저 스토리",
    },
    # description + custom attr 양쪽에 동일 UUID (중복)
    203: {
        **_US_TEMPLATE,
        "id": 203,
        "ref": 53,
        "subject": "US with duplicate IMS link",
        "description": f"기획서: {IMS_FAKE_BASE_URL}/support-ai/?uid=8226&uuid={IMS_UUID_IN_DESCRIPTION}",
    },
}

CUSTOM_ATTRIBUTE_VALUES_WITH_IMS = {
    201: {
        "version": 1,
        "attributes_values": {
            "1": "High",
            "2": f"IMS 링크: {IMS_FAKE_BASE_URL}/support-ai/?uid=8227&uuid={IMS_UUID_IN_CUSTOM_ATTR}",
        },
    },
    203: {
        "version": 1,
        "attributes_values": {
            "1": "Medium",
            "2": f"중복 링크: {IMS_FAKE_BASE_URL}/support-ai/?uid=8226&uuid={IMS_UUID_IN_DESCRIPTION}",
        },
    },
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
        "status_extra_info": {"name": "New"},
        "assigned_to_extra_info": {"full_name_display": "Test User"} if assigned_to else None,
    }


TASKS = {
    100: [
        {
            "id": 501,
            "ref": 501,
            "subject": "Task 1 for US 100",
            "status_extra_info": {"name": "In Progress"},
            "assigned_to_extra_info": {"full_name_display": "Test User"},
            "project_extra_info": {"slug": "test-project"},
        }
    ],
}

COMMENTS = {
    100: [
        {
            "id": 901,
            "user": {"name": "Alice"},
            "created_at": "2025-06-20T10:00:00Z",
            "comment": "Initial comment for US 100",
        }
    ],
}
