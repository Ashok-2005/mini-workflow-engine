# Mini Agent Workflow Engine (Assignment)

This is a small backend-only project for an AI Engineering Internship coding assignment.

It implements a minimal workflow / graph engine (somewhat like a tiny LangGraph) using FastAPI and plain Python.

---

## Features

### 1. Minimal Workflow / Graph Engine

- **Nodes**: Each node is a Python function ("tool") that reads and updates a shared state (`dict`).
- **State**: A shared `dict` that flows from one node to the next.
- **Edges**:
  - Defined via `GraphConfig` + `NodeConfig`
  - Each node has `next` (default successor).
- **Branching**:
  - Nodes may specify `condition_key`, `next_if_true`, `next_if_false`.
  - The engine reads `state[condition_key]` as a boolean and routes accordingly.
- **Looping**:
  - A node can loop on itself (or back to any node) by setting `next_if_false`
    or `next_if_true` to its own name.
  - A simple global `max_steps` guard prevents infinite loops.

All graphs and runs are stored **in memory** for simplicity.

---

## 2. Tool Registry

- `ToolRegistry` keeps a dictionary of tools (`name -> function`).
- Tools are just Python functions with signature:

  ```python
  def tool_name(state: dict) -> dict:
      ...
      return {"some_key": value}
