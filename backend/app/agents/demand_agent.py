import re
from .base import BaseAgent, AgentResult, WorkflowState


class DemandUnderstandingAgent(BaseAgent):
    name = "需求理解 Agent"
    step_name = "识别任务意图与交付约束"

    def run(self, state: WorkflowState) -> AgentResult:
        text = f"{state.title}\n{state.goal}\n{state.context}"
        intent = self._detect_intent(text, state.task_type)
        constraints = self._extract_constraints(text)
        deliverable = state.deliverable or self._suggest_deliverable(intent)
        state.memory["intent"] = intent
        state.memory["constraints"] = constraints
        state.memory["deliverable"] = deliverable
        summary = f"识别为【{intent}】任务，交付物为【{deliverable}】，抽取约束 {len(constraints)} 条。"
        return AgentResult(self.name, self.step_name, {"intent": intent, "constraints": constraints, "deliverable": deliverable}, summary)

    def _detect_intent(self, text: str, fallback: str) -> str:
        rules = [
            ("周报", "运营周报"),
            ("日报", "运营日报"),
            ("会议纪要", "会议纪要"),
            ("复盘", "项目复盘"),
            ("方案", "执行方案"),
            ("数据", "数据分析"),
            ("工单", "工单处理"),
            ("客服", "客服知识辅助"),
            ("风险", "风险评估"),
        ]
        for key, value in rules:
            if key in text:
                return value
        return fallback or "综合知识任务"

    def _extract_constraints(self, text: str) -> list[str]:
        constraints: list[str] = []
        for pattern in [r"不超过\d+字", r"\d+字以内", r"需要[^，。；\n]+", r"必须[^，。；\n]+", r"不要[^，。；\n]+"]:
            constraints.extend(re.findall(pattern, text))
        if "正式" in text or "汇报" in text:
            constraints.append("采用正式、管理汇报风格")
        if "表格" in text:
            constraints.append("包含结构化表格")
        return list(dict.fromkeys(constraints))[:8]

    def _suggest_deliverable(self, intent: str) -> str:
        mapping = {
            "运营周报": "运营周报 Markdown",
            "会议纪要": "会议纪要 Markdown",
            "执行方案": "执行方案文档",
            "数据分析": "数据分析报告",
        }
        return mapping.get(intent, "结构化分析报告")
