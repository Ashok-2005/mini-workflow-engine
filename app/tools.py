# app/tools.py
from __future__ import annotations

from typing import Any, Dict, List

from .engine import ToolRegistry

tools = ToolRegistry()


@tools.register("split_text")
def split_text_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Split input text into chunks of words.

    Input in state:
      - text: str
      - chunk_size: int (optional, default 80 words)

    Output:
      - chunks: List[str]
    """
    text: str = state.get("text", "") or ""
    chunk_size: int = int(state.get("chunk_size", 80))

    words = text.split()
    chunks: List[str] = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)

    return {"chunks": chunks}


@tools.register("summarize_chunks")
def summarize_chunks_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Very naive summarizer: for each chunk take the first sentence
    or first 25 words.
    """
    chunks: List[str] = state.get("chunks", []) or []
    summaries: List[str] = []

    for chunk in chunks:
        sentences = [s.strip() for s in chunk.split(".") if s.strip()]
        if sentences:
            candidate = sentences[0]
        else:
            candidate = " ".join(chunk.split()[:25])
        summaries.append(candidate)

    return {"summaries": summaries}


@tools.register("merge_summaries")
def merge_summaries_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge list of summaries into a single string.
    """
    summaries: List[str] = state.get("summaries", []) or []
    merged = ". ".join(summaries)

    return {"merged_summary": merged}


@tools.register("refine_summary")
def refine_summary_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Refine the merged summary until it is under a target word length.

    Input:
      - merged_summary: str
      - target_length: int (default 120 words)
      - max_iterations: int (default 5)

    Uses 'iteration' counter in state.

    Output:
      - final_summary: str
      - iteration: int
      - summary_within_limit: bool
    """
    merged_summary: str = state.get("merged_summary", "") or ""
    target_length: int = int(state.get("target_length", 120))
    max_iterations: int = int(state.get("max_iterations", 5))

    iteration: int = int(state.get("iteration", 0)) + 1
    words = merged_summary.split()

    if len(words) <= target_length or iteration >= max_iterations:
        # we are done; either under limit or we hit max_iterations
        return {
            "final_summary": " ".join(words[:target_length]),
            "iteration": iteration,
            "summary_within_limit": True,
        }

    # simple refinement: keep only the first 'target_length' words
    refined = " ".join(words[:target_length])

    return {
        "merged_summary": refined,
        "final_summary": refined,
        "iteration": iteration,
        "summary_within_limit": False,
    }
