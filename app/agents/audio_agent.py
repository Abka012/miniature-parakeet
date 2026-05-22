"""Audio processing agent."""

from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from app.state.state import AgentState


class AudioAgent:
    """Agent specialized in audio processing."""

    system_prompt: str = """You are an audio processing agent.

    Your role is to analyze and process audio based on user requests.
    You can:
    - Extract audio metadata (duration, sample rate, etc.)
    - Detect audio content (speech, music, noise)
    - Identify audio characteristics (volume, pitch)
    - Process audio streams

    Always use the available tools for processing audio.
    """

    def __init__(self) -> None:
        self.name: str = "audio_agent"
        self.prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("user", "{input}"),
            ]
        )

    async def process_audio(self, audio_data: str, format: str = "wav") -> str:
        """Process audio data and return results."""
        from app.tools.mcp_client import mcp_client

        result = await mcp_client.process_audio(audio_data, format)
        if result.get("status") == "error":
            return f"Error: {result.get('error', 'unknown error')}"
        return result.get("result", "No result returned")

    async def extract_info(self, audio_data: str) -> dict:
        """Extract metadata from audio."""
        from app.tools.mcp_client import mcp_client

        return await mcp_client.process_audio(audio_data, "wav")

    async def run(self, state: AgentState) -> dict[str, Any]:
        """Run the audio agent."""
        task_data = state.get("task_data", {})

        audio_data = task_data.get("audio_data", "")

        result: dict[str, Any] = {
            "current_agent": self.name,
            "results": {
                "audio_agent": {
                    "status": "completed",
                    "task_type": "audio",
                },
            },
        }

        if audio_data:
            processed = await self.process_audio(audio_data, "wav")
            result["results"]["audio_agent"]["processing_result"] = processed

        return result

    async def process(self, audio_data: str) -> dict[str, Any]:
        """Process audio directly."""
        result = await self.process_audio(audio_data, "wav")
        return {
            "status": "success" if not result.startswith("Error") else "error",
            "agent": self.name,
            "result": result,
        }
