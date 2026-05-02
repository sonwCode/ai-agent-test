from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResult:
    agent_name: str
    step_name: str
    output: dict[str, Any]
    summary: str
    status: str = "success"


@dataclass
class WorkflowState:
    task_id: int
    title: str
    goal: str
    task_type: str
    context: str
    deliverable: str
    memory: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    final_content: str = ""
    quality_score: float = 0.0


class BaseAgent:
    name = "BaseAgent"
    step_name = "base_step"

    def run(self, state: WorkflowState) -> AgentResult:
        raise NotImplementedError
