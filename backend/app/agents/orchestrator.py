import json
from typing import Any

from .base import WorkflowState, AgentResult
from .demand_agent import DemandUnderstandingAgent
from .retrieval_agent import KnowledgeRetrievalAgent
from .analysis_agent import StructuredAnalysisAgent
from .generation_agent import DocumentGenerationAgent
from .quality_agent import QualityReviewAgent
from ..database import execute, query_all, query_one, utc_now
from ..schemas import TaskRunRequest
from ..services.artifact_service import artifact_service
from ..services.audit_service import audit_service


class AgentOrchestrator:
    def __init__(self) -> None:
        self.agents = [
            DemandUnderstandingAgent(),
            KnowledgeRetrievalAgent(),
            StructuredAnalysisAgent(),
            DocumentGenerationAgent(),
            QualityReviewAgent(),
        ]

    def run(self, req: TaskRunRequest) -> dict[str, Any]:
        now = utc_now()
        task_id = execute(
            """
            INSERT INTO agent_tasks(title, goal, task_type, context, deliverable, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (req.title, req.goal, req.task_type, req.context, req.deliverable, "running", now, now),
        )
        audit_service.log("task.created", f"创建任务：{req.title}", task_id)
        state = WorkflowState(
            task_id=task_id,
            title=req.title,
            goal=req.goal,
            task_type=req.task_type,
            context=req.context,
            deliverable=req.deliverable,
        )

        try:
            for agent in self.agents:
                started = utc_now()
                result = agent.run(state)
                self._record_step(task_id, result, started)
                audit_service.log("agent.step", f"{result.agent_name}：{result.summary}", task_id)

            artifact_id = artifact_service.create_markdown(task_id, f"{req.title}.md", state.final_content)
            summary = self._summary_from_state(state, artifact_id)
            execute(
                "UPDATE agent_tasks SET status = ?, quality_score = ?, result_summary = ?, updated_at = ? WHERE id = ?",
                ("completed", state.quality_score, summary, utc_now(), task_id),
            )
            audit_service.log("task.completed", summary, task_id)
        except Exception as exc:
            execute(
                "UPDATE agent_tasks SET status = ?, result_summary = ?, updated_at = ? WHERE id = ?",
                ("failed", str(exc), utc_now(), task_id),
            )
            audit_service.log("task.failed", str(exc), task_id)
            raise
        return self.get_task(task_id) or {"id": task_id}

    def _record_step(self, task_id: int, result: AgentResult, started: str) -> None:
        execute(
            """
            INSERT INTO agent_steps(task_id, agent_name, step_name, input_text, output_text, status, started_at, finished_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                result.agent_name,
                result.step_name,
                "",
                json.dumps({"summary": result.summary, "output": result.output}, ensure_ascii=False, indent=2),
                result.status,
                started,
                utc_now(),
            ),
        )

    def _summary_from_state(self, state: WorkflowState, artifact_id: int) -> str:
        return f"任务已完成：质量评分 {state.quality_score}，生成物 ID={artifact_id}，证据片段 {len(state.evidence)} 条。"

    def list_tasks(self) -> list[dict[str, Any]]:
        return query_all("SELECT * FROM agent_tasks ORDER BY id DESC LIMIT 50")

    def get_task(self, task_id: int) -> dict[str, Any] | None:
        task = query_one("SELECT * FROM agent_tasks WHERE id = ?", (task_id,))
        if not task:
            return None
        task["steps"] = query_all("SELECT * FROM agent_steps WHERE task_id = ? ORDER BY id ASC", (task_id,))
        task["artifacts"] = query_all("SELECT id, task_id, name, artifact_type, created_at FROM artifacts WHERE task_id = ? ORDER BY id DESC", (task_id,))
        task["audit_logs"] = query_all("SELECT * FROM audit_logs WHERE task_id = ? ORDER BY id DESC LIMIT 50", (task_id,))
        return task


orchestrator = AgentOrchestrator()
