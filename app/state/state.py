"""Agent state management for shared context across agents."""

from typing import Annotated, Any

from langgraph.graph import MessagesState


def _merge_results(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """Merge two result dicts — used as a reducer for concurrent writes."""
    return {**a, **b}


def _last_wins(a: str | None, b: str | None) -> str | None:
    """Last concurrent write wins — for single-value keys."""
    return b if b is not None else a


class AgentState(MessagesState):
    """
    Shared state for the multi-agent system.

    This state is shared across all agents and the supervisor.
    It contains:
    - messages: Conversation history
    - task_type: Type of request (image/audio/video)
    - task_data: Input data for processing
    - results: Aggregated results from all agents
    - metadata: Additional context information
    """

    # Base MessagesState already has 'messages' with a built-in reducer
    # We add our custom fields below
    task_type: str
    task_data: dict[str, Any]
    results: Annotated[dict[str, Any], _merge_results]
    metadata: Annotated[dict[str, Any], _merge_results]
    current_agent: Annotated[str, _last_wins]
    error: Annotated[str | None, _last_wins]
