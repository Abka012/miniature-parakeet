"""Supervisor agent that orchestrates sub-agents."""

from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.agents.audio_agent import AudioAgent
from app.agents.image_agent import ImageAgent
from app.agents.video_agent import VideoAgent
from app.state.state import AgentState


class SupervisorAgent:
    """
    Supervisor agent that coordinates multiple sub-agents.

    The supervisor:
    - Receives the user request
    - Determines which agents to invoke
    - Distributes work among sub-agents
    - Collects results from all agents
    - Routes to final aggregator
    """

    def __init__(self) -> None:
        self.image_agent: ImageAgent = ImageAgent()
        self.audio_agent: AudioAgent = AudioAgent()
        self.video_agent: VideoAgent = VideoAgent()
        self.checkpointer: MemorySaver = MemorySaver()
        self.graph: Any = None
        self._build_graph()

    def _build_graph(self):
        """Build the agent workflow graph."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("image_agent", self.image_agent.run)
        workflow.add_node("audio_agent", self.audio_agent.run)
        workflow.add_node("video_agent", self.video_agent.run)
        workflow.add_node("aggregator", self._aggregator_node)

        # Define routing logic
        workflow.add_conditional_edges(
            "supervisor",
            self._route_to_agent,
            {
                "image": "image_agent",
                "audio": "audio_agent",
                "video": "video_agent",
                "aggregate": "aggregator",
            },
        )

        # Each agent routes back to supervisor or ends
        workflow.add_edge("image_agent", END)
        workflow.add_edge("audio_agent", END)
        workflow.add_edge("video_agent", END)

        workflow.add_edge("aggregator", END)

        # Set entry point
        workflow.set_entry_point("supervisor")

        self.graph = workflow.compile(checkpointer=self.checkpointer)

    def _supervisor_node(self, state: AgentState) -> dict[str, Any]:
        """Supervisor logic to determine which agent to invoke."""
        messages = state["messages"]
        task_type = state.get("task_type", "")

        # Simulate supervisor decision-making
        # In a real implementation, this would use an LLM

        # Check if we need to start processing
        if not task_type and messages:
            # Analyze last message to determine task type
            last_message = messages[-1]
            content = str(last_message.content).lower()

            if "image" in content or "photo" in content or "picture" in content:
                task_type = "image"
            elif "audio" in content or "sound" in content or "music" in content:
                task_type = "audio"
            elif "video" in content or "movie" in content or "clip" in content:
                task_type = "video"
            else:
                task_type = "all"  # Default to processing all

        # Update state
        return {
            "task_type": task_type,
            "current_agent": "supervisor",
            "metadata": {
                "task_type": task_type,
                "timestamp": "2026-05-21T00:00:00Z",
            },
        }

    def _route_to_agent(self, state: AgentState) -> str:
        """Determine which agent to route to next."""
        task_type = state.get("task_type", "")
        current_agent = state.get("current_agent", "")

        # If supervisor just started, route based on task type
        if current_agent == "supervisor":
            if task_type == "all":
                return "image"  # Start with image
            elif task_type:
                return task_type
            return "image"  # Default

        # After processing, route to aggregator
        return "aggregate"

    def _aggregator_node(self, state: AgentState) -> dict[str, Any]:
        """Aggregate results from all agents."""
        # In a real implementation, this would collect and merge results
        # For now, we simulate the aggregation

        return {
            "results": {
                "image": {"status": "completed"},
                "audio": {"status": "completed"},
                "video": {"status": "completed"},
            },
            "current_agent": "aggregator",
            "message": "All agents completed processing",
        }

    async def run(self, user_input: str, config: RunnableConfig | None = None) -> dict:
        """Run the supervisor workflow."""
        config = config or RunnableConfig(configurable={"thread_id": "1"})

        initial_state: AgentState = {
            "messages": [HumanMessage(content=user_input)],
            "task_type": "",
            "task_data": {},
            "results": {},
            "metadata": {},
            "current_agent": "",
            "error": None,
        }

        result = await self.graph.ainvoke(initial_state, config=config)
        return result
