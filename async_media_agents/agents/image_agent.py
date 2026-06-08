"""Image processing agent."""

from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from async_media_agents.state.state import AgentState


class ImageAgent:
    """Agent specialized in image processing."""

    system_prompt: str = """You are an image processing agent.

    Your role is to analyze and process images based on user requests.
    You can:
    - Extract image metadata
    - Identify objects, scenes, or people in images
    - Detect image properties (size, format, colors)
    - Apply filters or transformations

    Always use the available tools for processing images.
    """

    def __init__(self) -> None:
        self.name: str = "image_agent"
        self.prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("user", "{input}"),
            ]
        )

    async def process_image(self, image_data: str, format: str = "png") -> str:
        """Process image data and return results."""
        from async_media_agents.tools.mcp_client import mcp_client

        result = await mcp_client.process_image(image_data, format)
        if result.get("status") == "error":
            return f"Error: {result.get('error', 'unknown error')}"
        return result.get("result", "No result returned")

    async def extract_info(self, image_data: str) -> dict:
        """Extract metadata from image."""
        from async_media_agents.tools.mcp_client import mcp_client

        return await mcp_client.process_image(image_data, "png")

    async def run(self, state: AgentState) -> dict[str, Any]:
        """Run the image agent."""
        task_data = state.get("task_data", {})

        # Get image data from task
        image_data = task_data.get("image_data", "")

        result: dict[str, Any] = {
            "current_agent": self.name,
            "results": {
                "image_agent": {
                    "status": "completed",
                    "task_type": "image",
                },
            },
        }

        if image_data:
            processed = await self.process_image(image_data, "png")
            result["results"]["image_agent"]["processing_result"] = processed

        return result

    async def process(self, image_data: str) -> dict[str, Any]:
        """Process image directly."""
        result = await self.process_image(image_data, "png")
        return {
            "status": "success" if not result.startswith("Error") else "error",
            "agent": self.name,
            "result": result,
        }
