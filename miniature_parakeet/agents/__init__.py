"""Multi-agent system package."""

from miniature_parakeet.agents.audio_agent import AudioAgent
from miniature_parakeet.agents.image_agent import ImageAgent
from miniature_parakeet.agents.supervisor import SupervisorAgent
from miniature_parakeet.agents.video_agent import VideoAgent

__all__ = [
    "ImageAgent",
    "AudioAgent",
    "VideoAgent",
    "SupervisorAgent",
]
