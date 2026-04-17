"""Tests for TaigaCLIHandlers — validates handler logic with FakeTaigaClient."""

import json

import pytest


class TestResolveHelpers:
    """Tests for _get_id_from_ref and _resolve_assigned_to."""

    def test_resolve_us_id_by_ref(self, taiga_handlers):
        us_id = taiga_handlers._get_id_from_ref(ref=42)
        assert us_id == 100

    def test_resolve_us_id_invalid_ref_raises(self, taiga_handlers):
        with pytest.raises(ValueError, match="not found"):
            taiga_handlers._get_id_from_ref(ref=9999)

    def test_resolve_assigned_to_me(self, taiga_handlers):
        result = taiga_handlers._resolve_assigned_to(me=True)
        assert result == 10  # ME["id"]

    def test_resolve_assigned_to_explicit(self, taiga_handlers):
        result = taiga_handlers._resolve_assigned_to(assigned_to=55)
        assert result == 55

    def test_resolve_assigned_to_none(self, taiga_handlers):
        result = taiga_handlers._resolve_assigned_to()
        assert result is None


class TestCreateUserstory:
    """Tests for create_userstory."""

    def test_create_userstory_simple(self, taiga_handlers, fake_taiga_client, capsys):
        taiga_handlers.create_userstory(subject="New Feature")
        assert len(fake_taiga_client.created_stories) == 1
        assert fake_taiga_client.created_stories[0]["subject"] == "New Feature"
        out = capsys.readouterr().out
        assert "created" in out.lower()

    def test_create_userstory_with_tasks(self, taiga_handlers, fake_taiga_client):
        taiga_handlers.create_userstory(
            subject="US with tasks",
            tasks=["Task A", "Task B::Description B", "Task C"],
        )
        assert len(fake_taiga_client.created_stories) == 1
        assert len(fake_taiga_client.created_tasks) == 3

        # Check if descriptions are correctly parsed
        assert fake_taiga_client.created_tasks[0]["subject"] == "Task A"
        assert fake_taiga_client.created_tasks[0]["description"] == ""

        assert fake_taiga_client.created_tasks[1]["subject"] == "Task B"
        assert fake_taiga_client.created_tasks[1]["description"] == "Description B"

        assert fake_taiga_client.created_tasks[2]["subject"] == "Task C"
        assert fake_taiga_client.created_tasks[2]["description"] == ""

        # All tasks linked to the created US
        us_id = fake_taiga_client.created_stories[0]["id"]
        for task in fake_taiga_client.created_tasks:
            assert task["user_story"] == us_id

    def test_create_userstory_with_tasks_json(self, taiga_handlers, fake_taiga_client):
        tasks_json = json.dumps(
            [
                {"subject": "JSON Task 1", "description": "Desc 1"},
                {"subject": "JSON Task 2"},
            ]
        )
        taiga_handlers.create_userstory(subject="US from JSON", tasks_json=tasks_json)
        assert len(fake_taiga_client.created_tasks) == 2
        assert fake_taiga_client.created_tasks[0]["subject"] == "JSON Task 1"

    def test_create_userstory_with_custom_attrs(self, taiga_handlers, fake_taiga_client):
        taiga_handlers.create_userstory(subject="US with custom attrs", custom_attrs=["123::Value A", "456::Value B"])
        assert len(fake_taiga_client.updated_ca_values) == 1
        assert fake_taiga_client.updated_ca_values[0]["attributes_values"] == {"123": "Value A", "456": "Value B"}

    def test_create_userstory_with_me(self, taiga_handlers, fake_taiga_client):
        taiga_handlers.create_userstory(subject="Assigned US", me=True)
        story = fake_taiga_client.created_stories[0]
        assert story["assigned_to"] == 10


class TestCreateTask:
    """Tests for create_task."""

    def test_create_single_task(self, taiga_handlers, fake_taiga_client, capsys):
        taiga_handlers.create_task(us_ref=42, subject="Standalone task")
        assert len(fake_taiga_client.created_tasks) == 1
        out = capsys.readouterr().out
        assert "Task created" in out

    def test_create_task_linked_to_us(self, taiga_handlers, fake_taiga_client):
        taiga_handlers.create_task(us_ref=42, subject="Linked task")
        task = fake_taiga_client.created_tasks[0]
        assert task["user_story"] == 100

    def test_create_task_linked_by_ref(self, taiga_handlers, fake_taiga_client):
        taiga_handlers.create_task(us_ref=42, subject="Linked by ref")
        task = fake_taiga_client.created_tasks[0]
        assert task["user_story"] == 100  # ref 42 → id 100

    def test_create_multiple_tasks(self, taiga_handlers, fake_taiga_client):
        taiga_handlers.create_task(us_ref=42, tasks=["T1::D1", "T2"])
        assert len(fake_taiga_client.created_tasks) == 2
        assert fake_taiga_client.created_tasks[0]["subject"] == "T1"
        assert fake_taiga_client.created_tasks[0]["description"] == "D1"
        assert fake_taiga_client.created_tasks[1]["subject"] == "T2"
        assert fake_taiga_client.created_tasks[1]["description"] == ""

    def test_create_task_no_input_raises(self, taiga_handlers):
        with pytest.raises(ValueError, match="At least one"):
            taiga_handlers.create_task(us_ref=42)


class TestUpdateUserstory:
    """Tests for update_userstory."""

    def test_update_subject(self, taiga_handlers, fake_taiga_client):
        taiga_handlers.update_userstory(ref=42, subject="Updated title")
        assert len(fake_taiga_client.updated_stories) == 1
        assert fake_taiga_client.updated_stories[0]["subject"] == "Updated title"

    def test_update_with_me(self, taiga_handlers, fake_taiga_client):
        taiga_handlers.update_userstory(ref=42, me=True)
        assert fake_taiga_client.updated_stories[0]["assigned_to"] == 10

    def test_update_custom_attrs(self, taiga_handlers, fake_taiga_client):
        taiga_handlers.update_userstory(ref=42, custom_attrs=["1::new value"])
        assert len(fake_taiga_client.updated_ca_values) == 1
        assert fake_taiga_client.updated_ca_values[0]["us_id"] == 100
        assert fake_taiga_client.updated_ca_values[0]["attributes_values"] == {"1": "new value"}
