"""MCP (Model Context Protocol) server for multi-agent system.

Processing logic lives in ``async_media_agents.tools.processors`` and is kept fully
decoupled from the MCP tool registration layer.
"""

from mcp.server import FastMCP

from async_media_agents.tools.processors import process_audio as _process_audio
from async_media_agents.tools.processors import process_image as _process_image
from async_media_agents.tools.processors import process_video as _process_video


class MCPServer:
    """MCP server providing tools for image, audio, and video processing."""

    def __init__(self) -> None:
        self.mcp: FastMCP = FastMCP(name="async-media-agents-mcp")
        self._tools: list[str] = []
        self._register_tools()

    def _register_tools(self):
        """Register all processing tools with MCP."""
        self._register_image_tool()
        self._register_audio_tool()
        self._register_video_tool()

    def _register_image_tool(self):
        """Register image processing tool."""

        @self.mcp.tool()
        def process_image(image_data: str, format: str = "png") -> dict:
            """Decode, inspect, and thumbnail a base64-encoded image."""
            return _process_image(image_data, format)

        self._tools.append("process_image")

    def _register_audio_tool(self):
        """Register audio processing tool."""

        @self.mcp.tool()
        def process_audio(audio_data: str, format: str = "wav") -> dict:
            """Decode a base64-encoded WAV and extract audio metadata."""
            return _process_audio(audio_data, format)

        self._tools.append("process_audio")

    def _register_video_tool(self):
        """Register video processing tool."""

        @self.mcp.tool()
        def process_video(video_data: str, format: str = "mp4") -> dict:
            """Decode a base64-encoded video and extract metadata."""
            return _process_video(video_data, format)

        self._tools.append("process_video")

    def get_tools(self) -> list[str]:
        """Get all registered tool names."""
        return self._tools

    async def run_image_tool(self, image_data: str, format: str = "png") -> dict:
        """Execute image processing (async wrapper around core processor)."""
        return _process_image(image_data, format)

    async def run_audio_tool(self, audio_data: str, format: str = "wav") -> dict:
        """Execute audio processing (async wrapper around core processor)."""
        return _process_audio(audio_data, format)

    async def run_video_tool(self, video_data: str, format: str = "mp4") -> dict:
        """Execute video processing (async wrapper around core processor)."""
        return _process_video(video_data, format)


# Singleton instance
mcp_server = MCPServer()
