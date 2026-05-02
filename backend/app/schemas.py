from pydantic import BaseModel, Field
from typing import Any


class TaskRunRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=120)
    goal: str = Field(..., min_length=5, max_length=2000)
    task_type: str = Field(default="运营分析", max_length=80)
    context: str = Field(default="", max_length=5000)
    deliverable: str = Field(default="管理汇报材料", max_length=120)


class TaskBrief(BaseModel):
    id: int
    title: str
    goal: str
    task_type: str
    status: str
    quality_score: float
    result_summary: str | None = None
    created_at: str
    updated_at: str


class TaskDetail(TaskBrief):
    steps: list[dict[str, Any]]
    artifacts: list[dict[str, Any]]
    audit_logs: list[dict[str, Any]]


class KnowledgeDoc(BaseModel):
    id: int
    filename: str
    title: str
    created_at: str
    chunk_count: int = 0


class Dashboard(BaseModel):
    total_tasks: int
    completed_tasks: int
    running_tasks: int
    total_docs: int
    total_chunks: int
    avg_quality_score: float
    recent_tasks: list[TaskBrief]
