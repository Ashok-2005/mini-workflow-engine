# app/engine.py
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field


class NodeConfig(BaseModel):
    """
    One node in the workflow graph.

    - tool: name of a registered tool to call
    - next: default next node
    - condition_key: if set, read this boolean from state
      and route to next_if_true / next_if_false
    """
    name: str
    tool: str
    next: Optional[str] = None
    condition_key: Optional[str] = None
    next_if_true: Optional[str] = None
    next_if_false: Optional[str] = None


class GraphConfig(BaseModel):
    """
    Definition of a workflow.

    - start_node: name of node to start from
    """
    id: Optional[str] = None
    start_node: str
    nodes: List[NodeConfig]


class RunStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class StepLog(BaseModel):
    step_index: int
    node: str
    timestamp: datetime
    state: Dict[str, Any]


class RunState(BaseModel):
    id: str
    graph_id: str
    status: RunStatus
    current_node: Optional[str] = None
    state: Dict[str, Any] = Field(default_factory=dict)
    log: List[StepLog] = Field(default_factory=list)
    error: Optional[str] = None


class ToolRegistry:
    """
    Simple tool registry.

    Each tool is a sync or async function:  (state: dict) -> dict
    """

    def __init__(self) -> None:
        self._tools: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

    def register(self, name: str):
        """Decorator to register a tool."""

        def decorator(func: Callable[[Dict[str, Any]], Any]):
            self._tools[name] = func
            return func

        return decorator

    def get(self, name: str) -> Optional[Callable[[Dict[str, Any]], Any]]:
        return self._tools.get(name)


class GraphEngine:
    """
    Minimal in-memory workflow engine.
    """

    def __init__(self, tools: ToolRegistry) -> None:
        self.tools = tools
        self.graphs: Dict[str, GraphConfig] = {}
        self.runs: Dict[str, RunState] = {}

    def create_graph(self, config: GraphConfig) -> str:
        graph_id = str(uuid.uuid4())
        config.id = graph_id

        # basic validation: unique node names & valid start node
        node_names = {n.name for n in config.nodes}
        if config.start_node not in node_names:
            raise ValueError("start_node must be one of the nodes")

        if len(node_names) != len(config.nodes):
            raise ValueError("node names must be unique")

        self.graphs[graph_id] = config
        return graph_id

    def get_graph(self, graph_id: str) -> GraphConfig:
        graph = self.graphs.get(graph_id)
        if not graph:
            raise KeyError("Graph not found")
        return graph

    def get_run(self, run_id: str) -> RunState:
        run = self.runs.get(run_id)
        if not run:
            raise KeyError("Run not found")
        return run

    async def _call_tool(
        self, tool: Callable[[Dict[str, Any]], Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Support both sync and async tools
        if asyncio.iscoroutinefunction(tool):
            result = await tool(state)
        else:
            result = await run_in_threadpool(tool, state)

        if not isinstance(result, dict):
            raise RuntimeError("Tool must return a dict representing new/updated state")
        return result

    async def run_graph(
        self, graph_id: str, initial_state: Dict[str, Any]
    ) -> RunState:
        graph = self.get_graph(graph_id)
        run_id = str(uuid.uuid4())

        run_state = RunState(
            id=run_id,
            graph_id=graph_id,
            status=RunStatus.RUNNING,
            current_node=graph.start_node,
            state=dict(initial_state),
            log=[],
        )
        self.runs[run_id] = run_state

        nodes_by_name: Dict[str, NodeConfig] = {n.name: n for n in graph.nodes}
        current_node_name: Optional[str] = graph.start_node

        step_index = 0
        max_steps = 1000  # safety guard against infinite loops

        try:
            while current_node_name is not None:
                if step_index >= max_steps:
                    raise RuntimeError("Max steps exceeded, possible infinite loop")

                node_cfg = nodes_by_name.get(current_node_name)
                if node_cfg is None:
                    raise RuntimeError(f"Node '{current_node_name}' not found")

                run_state.current_node = current_node_name

                tool = self.tools.get(node_cfg.tool)
                if tool is None:
                    raise RuntimeError(f"Tool '{node_cfg.tool}' not registered")

                # Call node (tool) to update shared state
                new_state = await self._call_tool(tool, run_state.state)
                run_state.state.update(new_state)

                # Log snapshot after node execution
                run_state.log.append(
                    StepLog(
                        step_index=step_index,
                        node=current_node_name,
                        timestamp=datetime.utcnow(),
                        state=dict(run_state.state),
                    )
                )

                # Decide next node (branching + looping)
                next_node: Optional[str]
                if node_cfg.condition_key is not None:
                    cond_value = bool(
                        run_state.state.get(node_cfg.condition_key, False)
                    )
                    next_node = (
                        node_cfg.next_if_true if cond_value else node_cfg.next_if_false
                    )
                else:
                    next_node = node_cfg.next

                current_node_name = next_node
                step_index += 1

            run_state.status = RunStatus.COMPLETED
            run_state.current_node = None

        except Exception as exc:
            run_state.status = RunStatus.FAILED
            run_state.error = str(exc)

        return run_state
