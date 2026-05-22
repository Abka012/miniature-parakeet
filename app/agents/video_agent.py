"""Video processing agent."""

from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from app.state.state import AgentState


class VideoAgent:
    """Agent specialized in video processing."""

    system_prompt: str = """You are a video processing agent.

    Your role is to analyze and process video based on user requests.
    You can:
    - Extract video metadata (duration, resolution, fps)
    - Analyze video content (frames, scenes, objects)
    - Detect video characteristics (format, codec)
    - Process video streams

    Always use the available tools for processing video.
    """

    def __init__(self) -> None:
        self.name: str = "video_agent"
        self.prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("user", "{input}"),
            ]
        )

    async def process_video(self, video_data: str, format: str = "mp4") -> str:
        """Process video data and return results."""
        from app.tools.mcp_client import mcp_client

        result = await mcp_client.process_video(video_data, format)
        if result.get("status") == "error":
            return f"Error: {result.get('error', 'unknown error')}"
        return result.get("result", "No result returned")

    async def extract_info(self, video_data: str) -> dict:
        """Extract metadata from video."""
        from app.tools.mcp_client import mcp_client

        return await mcp_client.process_video(video_data, "mp4")

    async def run(self, state: AgentState) -> dict[str, Any]:
        """Run the video agent."""
        task_data = state.get("task_data", {})

        # Get video data from task
        video_data = task_data.get("video_data", "")

        result: dict[str, Any] = {
            "current_agent": self.name,
            "results": {
                "video_agent": {
                    "status": "completed",
                    "task_type": "video",
                },
            },
        }

        if video_data:
            processed = await self.process_video(video_data, "mp4")
            result["results"]["video_agent"]["processing_result"] = processed

        return result

    async def process(self, video_data: str) -> dict[str, Any]:
        """Process video directly."""
        result = await self.process_video(video_data, "mp4")
        return {
            "status": "success" if not result.startswith("Error") else "error",
            "agent": self.name,
            "result": result,
        }
