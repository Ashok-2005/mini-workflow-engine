# app/main.py
from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .engine import GraphConfig, GraphEngine, RunState
from .engine import NodeConfig  # re-export convenience
from .tools import tools

app = FastAPI(title="Mini Agent Workflow Engine")

# Instantiate engine with shared tool registry
engine = GraphEngine(tools=tools)


# ---------- Pydantic request/response models ----------


class GraphCreateRequest(GraphConfig):
    """Same as GraphConfig, but without id in body."""
    pass


class GraphCreateResponse(BaseModel):
    graph_id: str


class GraphRunRequest(BaseModel):
    graph_id: str
    initial_state: Dict[str, Any] = {}


class GraphRunResponse(BaseModel):
    run_id: str
    final_state: Dict[str, Any]
    status: str
    log: Any


class GraphStateResponse(BaseModel):
    run_id: str
    status: str
    current_node: Any
    state: Dict[str, Any]
    log_length: int
    error: Any = None


# ---------- Example workflow registration (Option B) ----------


@app.on_event("startup")
def register_example_graph() -> None:
    """
    Register an example 'Summarization + Refinement' workflow at startup.

    Steps:
      1. split_text -> 2. summarize_chunks -> 3. merge_summaries -> 4. refine_summary (loop)
    """
    example_graph = GraphConfig(
        start_node="split_text",
        nodes=[
            NodeConfig(
                name="split_text",
                tool="split_text",
                next="summarize_chunks",
            ),
            NodeConfig(
                name="summarize_chunks",
                tool="summarize_chunks",
                next="merge_summaries",
            ),
            NodeConfig(
                name="merge_summaries",
                tool="merge_summaries",
                next="refine_summary",
            ),
            NodeConfig(
                name="refine_summary",
                tool="refine_summary",
                # Loop based on 'summary_within_limit' flag in shared state
                condition_key="summary_within_limit",
                next_if_true=None,          # stop workflow
                next_if_false="refine_summary",  # loop
            ),
        ],
    )

    graph_id = engine.create_graph(example_graph)
    # Just to make it discoverable in logs
    print(f"Example summarization graph registered with id: {graph_id}")


# ---------- API endpoints ----------


@app.post("/graph/create", response_model=GraphCreateResponse)
async def create_graph(body: GraphCreateRequest):
    """
    Create a new workflow graph.

    Body example:
    {
      "start_node": "split",
      "nodes": [
        {
          "name": "split",
          "tool": "split_text",
          "next": "summarize_chunks"
        }
      ]
    }
    """
    try:
        graph_id = engine.create_graph(GraphConfig(**body.dict(exclude={"id"})))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return GraphCreateResponse(graph_id=graph_id)


@app.post("/graph/run", response_model=GraphRunResponse)
async def run_graph(body: GraphRunRequest):
    """
    Run a graph from the beginning with an initial state.

    Example body to run the example summarization graph:

    {
      "graph_id": "<EXAMPLE_GRAPH_ID>",
      "initial_state": {
        "text": "long text here...",
        "chunk_size": 80,
        "target_length": 100,
        "max_iterations": 5
      }
    }
    """
    try:
        run_state: RunState = await engine.run_graph(
            graph_id=body.graph_id, initial_state=body.initial_state
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Graph not found")

    return GraphRunResponse(
        run_id=run_state.id,
        final_state=run_state.state,
        status=run_state.status.value,
        log=[step.dict() for step in run_state.log],
    )


@app.get("/graph/state/{run_id}", response_model=GraphStateResponse)
async def get_graph_state(run_id: str):
    """
    Get the current state of a workflow run.
    For now runs are synchronous, so this typically returns the final state,
    but the structure supports long-running / async workflows later.
    """
    try:
        run_state = engine.get_run(run_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Run not found")

    return GraphStateResponse(
        run_id=run_state.id,
        status=run_state.status.value,
        current_node=run_state.current_node,
        state=run_state.state,
        log_length=len(run_state.log),
        error=run_state.error,
    )
from fastapi import FastAPI

# ... existing code ...

from fastapi.responses import RedirectResponse
from fastapi import Request

@app.get("/")
def root(request: Request):
    if "text/html" in request.headers.get("accept", ""):
        return RedirectResponse(url="/docs")
    return {"message": "Mini Agent Workflow Engine API"}
