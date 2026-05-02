from .base import BaseAgent, AgentResult, WorkflowState
from ..llm_client import llm_client


class DocumentGenerationAgent(BaseAgent):
    name = "文档生成 Agent"
    step_name = "生成业务交付物初稿"

    def run(self, state: WorkflowState) -> AgentResult:
        analysis = state.memory.get("analysis", {})
        evidence = state.evidence
        evidence_md = "\n".join(
            [f"- 来源《{e['title']}》片段 {e['chunk_index']}：{e['content'][:220]}" for e in evidence[:5]]
        ) or "- 暂无直接证据，以下内容为流程化建议，需要人工确认。"

        system = "你是企业运营与项目管理顾问，输出正式、结构化、可执行的管理材料。"
        user = f"""
任务标题：{state.title}
任务目标：{state.goal}
任务类型：{state.memory.get('intent')}
交付物：{state.memory.get('deliverable')}
约束：{state.memory.get('constraints')}
结构化分析：{analysis}
证据材料：{evidence_md}

请生成一份可以交给业务人员二次修改的正式材料。
"""
        llm_part = llm_client.complete(system, user)
        content = self._compose(state, analysis, evidence_md, llm_part)
        state.final_content = content
        return AgentResult(self.name, self.step_name, {"content": content}, "已生成业务交付物初稿。")

    def _compose(self, state: WorkflowState, analysis: dict, evidence_md: str, llm_part: str) -> str:
        key_points = "\n".join([f"- {x}" for x in analysis.get("key_points", [])])
        risks = "\n".join([f"- {x}" for x in analysis.get("risks", [])])
        recs = "\n".join([f"- {x}" for x in analysis.get("recommendations", [])])
        return f"""# {state.title}

> 任务类型：{state.memory.get('intent', state.task_type)}  
> 交付物：{state.memory.get('deliverable', state.deliverable)}  
> 生成方式：多 Agent 工作流自动生成，需业务负责人最终确认。

## 1. 任务背景

{analysis.get('background', '暂无背景信息。')}

## 2. 关键要点

{key_points or '- 暂无明确要点。'}

## 3. 证据来源

{evidence_md}

## 4. 初稿内容

{llm_part}

## 5. 风险与边界

{risks or '- 暂无明显风险。'}

## 6. 后续建议

{recs or '- 建议补充资料后再次运行 Agent 工作流。'}

## 7. 人工确认清单

| 检查项 | 状态 |
|---|---|
| 关键事实是否有来源 | 待确认 |
| 数据口径是否准确 | 待确认 |
| 是否涉及敏感信息 | 待确认 |
| 是否符合正式提交格式 | 待确认 |
"""
