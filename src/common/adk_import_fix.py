"""ADK imports using actual available classes."""

from typing import Any, Optional, Dict
from dataclasses import dataclass

# Use the actual ADK classes that exist
from google.adk.agents import LlmAgent, BaseAgent, Agent, ParallelAgent, SequentialAgent
from google.adk.tools import BaseTool as _BaseTool, ToolContext
from google.adk.tools.transfer_to_agent_tool import transfer_to_agent

# Re-export BaseTool with proper typing
BaseTool = _BaseTool


# Create a wrapper class for TransferToAgentTool since it doesn't exist
class TransferToAgentTool:
    """Wrapper for transfer_to_agent function."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    def __call__(self, context: ToolContext) -> Any:
        return transfer_to_agent(self.agent_name, context)


# Since Message doesn't exist in ADK, we'll create a simple dataclass for it


@dataclass
class Message:
    """Simple message class for agent communication."""

    role: str = "assistant"
    content: str = ""
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ToolResult:
    """Result from tool execution."""

    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None


# Extended ToolContext with data attribute
@dataclass
class Content:
    """Simple content class for telemetry and communication."""

    text: str = ""


@dataclass
class ExtendedToolContext(ToolContext):
    """Extended ToolContext with data attribute for SentinelOps."""
    data: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.data is None:
            self.data = {}


# Re-export for compatibility
__all__ = [
    "LlmAgent",
    "BaseAgent",
    "Agent",
    "ParallelAgent",
    "SequentialAgent",
    "BaseTool",
    "ToolContext",
    "ExtendedToolContext",
    "TransferToAgentTool",
    "Message",
    "ToolResult",
]
