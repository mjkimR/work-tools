"""Tests for TaigaCLIHandlers — validates handler logic with FakeTaigaClient."""

import json

import pytest


class TestResolveHelpers:
    """Tests for _resolve_us_id and _resolve_assigned_to."""

    def test_resolve_us_id_by_id(self, taiga_handlers):
        assert taiga_handlers._resolve_us_id(id=100) == 100

    def test_resolve_us_id_by_ref(self, taiga_handlers):
        us_id = taiga_handlers._resolve_us_id(ref=42)
        assert us_id == 100

    def test_resolve_us_id_missing_both_raises(self, taiga_handlers):
        with pytest.raises(ValueError, match="Either id or ref"):
            taiga_handlers._resolve_us_id()

    def test_resolve_us_id_invalid_ref_raises(self, taiga_handlers):
        with pytest.raises(ValueError, match="not found"):
            taiga_handlers._resolve_us_id(ref=9999)

    def test_resolve_assigned_to_me(self, taiga_handlers):
        result = taiga_handlers._resolve_assigned_to(me=True)
        assert result == 10  # ME["id"]

    def test_resolve_assigned_to_explicit(self, taiga_handlers):
        result = taiga_handlers._resolve_assigned_to(assigned_to=55)
        assert result == 55

    def test_resolve_assigned_to_none(self, taiga_handlers):
        result = taiga_handlers._resolve_assigned_to()
        assert result is None


class TestListAndSearch:
    """Tests for list/search commands."""

    def test_list_projects(self, taiga_handlers, capsys):
        taiga_handlers.list_projects()
        out = capsys.readouterr().out
        assert "Test Project" in out
        assert "Other Project" in out

    def test_search_userstories_all(self, taiga_handlers, capsys):
        taiga_handlers.search_userstories()
        out = capsys.readouterr().out
        assert "login" in out.lower()

    def test_search_userstories_with_query(self, taiga_handlers, capsys):
        taiga_handlers.search_userstories(query="bug")
        out = capsys.readouterr().out
        assert "dashboard" in out.lower()
        assert "login" not in out.lower()

    def test_search_userstories_no_results(self, taiga_handlers, capsys):
        taiga_handlers.search_userstories(query="nonexistent_xyz")
        out = capsys.readouterr().out
        assert "No results" in out


class TestGetUserstory:
    """Tests for get_userstory."""

    def test_get_userstory_by_id(self, taiga_handlers, capsys):
        taiga_handlers.get_userstory(id=100)
        out = capsys.readouterr().out
        assert "Implement login feature" in out
        assert "Ref: #42" in out

    def test_get_userstory_by_ref(self, taiga_handlers, capsys):
        taiga_handlers.get_userstory(ref=43)
        out = capsys.readouterr().out
        assert "Fix dashboard bug" in out


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
            tasks=["Task A", "Task B", "Task C"],
        )
        assert len(fake_taiga_client.created_stories) == 1
        assert len(fake_taiga_client.created_tasks) == 3
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

    def test_create_userstory_with_me(self, taiga_handlers, fake_taiga_client):
        taiga_handlers.create_userstory(subject="Assigned US", me=True)
        story = fake_taiga_client.created_stories[0]
        assert story["assigned_to"] == 10


class TestCreateTask:
    """Tests for create_task."""

    def test_create_single_task(self, taiga_handlers, fake_taiga_client, capsys):
        taiga_handlers.create_task(subject="Standalone task")
        assert len(fake_taiga_client.created_tasks) == 1
        out = capsys.readouterr().out
        assert "Task created" in out

    def test_create_task_linked_to_us(self, taiga_handlers, fake_taiga_client):
        taiga_handlers.create_task(subject="Linked task", us=100)
        task = fake_taiga_client.created_tasks[0]
        assert task["user_story"] == 100

    def test_create_task_linked_by_ref(self, taiga_handlers, fake_taiga_client):
        taiga_handlers.create_task(subject="Linked by ref", us_ref=42)
        task = fake_taiga_client.created_tasks[0]
        assert task["user_story"] == 100  # ref 42 → id 100

    def test_create_multiple_tasks(self, taiga_handlers, fake_taiga_client):
        taiga_handlers.create_task(tasks=["T1", "T2"])
        assert len(fake_taiga_client.created_tasks) == 2

    def test_create_task_no_input_raises(self, taiga_handlers):
        with pytest.raises(ValueError, match="At least one"):
            taiga_handlers.create_task()


class TestUpdateUserstory:
    """Tests for update_userstory."""

    def test_update_subject(self, taiga_handlers, fake_taiga_client):
        taiga_handlers.update_userstory(id=100, subject="Updated title")
        assert len(fake_taiga_client.updated_stories) == 1
        assert fake_taiga_client.updated_stories[0]["subject"] == "Updated title"

    def test_update_with_me(self, taiga_handlers, fake_taiga_client):
        taiga_handlers.update_userstory(id=100, me=True)
        assert fake_taiga_client.updated_stories[0]["assigned_to"] == 10


class TestCustomAttributes:
    """Tests for custom attribute commands."""

    def test_list_custom_attributes(self, taiga_handlers, capsys):
        taiga_handlers.list_custom_attributes()
        out = capsys.readouterr().out
        assert "Priority" in out
        assert "Sprint-Goal" in out
        assert "TAIGA_CA_" in out

    def test_get_custom_attr_values(self, taiga_handlers, capsys):
        taiga_handlers.get_custom_attr_values(id=100)
        out = capsys.readouterr().out
        assert "High" in out

    def test_update_custom_attr_values(self, taiga_handlers, fake_taiga_client, capsys):
        values_json = json.dumps({"1": "Low", "2": "New goal"})
        taiga_handlers.update_custom_attr_values(values_json, id=100)
        assert len(fake_taiga_client.updated_ca_values) == 1
        assert fake_taiga_client.updated_ca_values[0]["attributes_values"]["1"] == "Low"

    def test_update_custom_attr_values_bad_json(self, taiga_handlers):
        with pytest.raises(ValueError, match="Error parsing"):
            taiga_handlers.update_custom_attr_values("{bad json", id=100)
