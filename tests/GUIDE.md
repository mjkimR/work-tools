# Test Writing Guide

This document outlines the testing architecture and rules for the `work-tools` project. AI agents and developers must read and follow this guide when contributing test code.

## Directory Structure & Layer Summaries

**Favor Integration Tests over Unit Tests.** 
We primarily focus on the `integrate/` layer to verify real-world use cases and workflows. `unit/` tests should be strictly reserved for highly complex and isolated logic (e.g., HTML parsers) where setting up an integration test would be inefficient.

The `tests/` directory is divided into four main layers:

```text
tests/
├── integrate/  # Primary testing layer for workflows and Handlers using Fakes.
├── unit/       # Minimal unit tests for complex, independent logic.
├── fake/       # Stateful fake implementations of external systems.
├── utils/      # Utilities ensuring safe execution in real environments.
└── conftest.py # Global pytest fixtures.
```

### 1. `tests/integrate/` (Integration Tests - Primary Focus)
* **Summary**: The core layer for testing actual workflows, CLI entrypoints, and state mutations.
* **Scope**: Business workflow handlers (e.g., `TaigaCLIHandlers`, `ImsCLIHandlers`).
* **Rules**: 
  * **No real external connections.** Do not make actual HTTP or browser calls.
  * Always use Dependency Injection to pass `FakeClient` objects (from `fake/`) into the handlers.
  * *Example: Refer to the `taiga_handlers` fixture in `conftest.py`.*

### 2. `tests/unit/` (Unit Tests)
* **Summary**: Reserved exclusively for independently testable, complex internal logic.
* **Scope**: Data parsers (e.g., `ImsDocumentParser`), data transformations, and pure utilities.
* **Rules**:
  * Skip unit tests for simple wrappers or glue code; let `integrate/` handle them.
  * Rely entirely on fixed data inputs (such as static HTML/JSON files in `fake/data/`). 

### 3. `tests/fake/` (Fakes & Fixtures)
* **Summary**: Stateful mock implementations providing a reliable "real feel" of the outside world.
* **Scope**: External HTTP simulators (`fake_taiga_client.py`), Browser session simulators (`fake_ims_client.py`).
* **Rules**: 
  * **Avoid `unittest.mock.patch`.** Instead, implement Fake clients that replicate the exact interfaces of the real implementation.
  * Static response assets (JSON responses, HTML DOM snippets) should be stored in `tests/fake/data/`.

### 4. `tests/utils/` (Test Environment Utilities)
* **Summary**: Infrastructure aids for operations that require physical OS boundaries.
* **Scope**: Helpers that safely orchestrate real world components without side effects (e.g., `git_repo.py` to create real but temporary Git repositories).

---

## E2E (End-to-End) Tests

There is no dedicated `e2e/` testing folder. Because this is a CLI application, running tests within the `integrate/` layer (using `typer.testing.CliRunner` coupled with `FakeClient` objects) acts as an effective E2E alternative. This approach prevents the flakiness and high maintenance costs of testing against real network APIs or browser processes.

---

## 🤖 AI Agent Cheatsheet

1. **Prioritize Integration Tests**: By default, aim to write your verification logic in `tests/integrate/`.
2. **Adding External Clients**: If writing a new integration, create the actual `Client` in `src/`, mirror it with a `FakeClient` in `tests/fake/`, and register it in `conftest.py`.
3. **Avoid Patching**: Prevent using `mocker.patch` dynamically. Standardize around dependency injection of Fake objects.
