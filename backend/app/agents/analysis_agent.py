from collections import Counter
from .base import BaseAgent, AgentResult, WorkflowState
from ..services.knowledge_service import tokenize


class StructuredAnalysisAgent(BaseAgent):
    name = "结构化分析 Agent"
    step_name = "整理背景、问题、风险与建议"

    def run(self, state: WorkflowState) -> AgentResult:
        evidence_text = "\n".join([e["content"] for e in state.evidence])
        tokens = tokenize(evidence_text + "\n" + state.goal)
        hot_words = [w for w, _ in Counter(tokens).most_common(10) if len(w) >= 1]
        risks = self._detect_risks(state.goal + evidence_text)
        analysis = {
            "background": self._background(state),
            "key_points": self._key_points(state, hot_words),
            "risks": risks,
            "recommendations": self._recommendations(state, risks),
            "hot_words": hot_words,
        }
        state.memory["analysis"] = analysis
        summary = f"形成 {len(analysis['key_points'])} 条关键要点、{len(risks)} 条风险提示、{len(analysis['recommendations'])} 条建议。"
        return AgentResult(self.name, self.step_name, analysis, summary)

    def _background(self, state: WorkflowState) -> str:
        if state.evidence:
            return "已基于企业知识库资料进行分析，证据片段来自已上传文档。"
        return "当前知识库证据不足，分析主要基于任务目标与通用企业运营流程生成。"

    def _key_points(self, state: WorkflowState, hot_words: list[str]) -> list[str]:
        points = [
            f"任务目标聚焦：{state.goal[:80]}",
            f"任务类型：{state.memory.get('intent', state.task_type)}",
            f"交付要求：{state.memory.get('deliverable', state.deliverable)}",
        ]
        if hot_words:
            points.append("高频主题词：" + "、".join(hot_words[:8]))
        if state.evidence:
            points.append(f"已召回 {len(state.evidence)} 条知识片段，可作为生成依据。")
        return points

    def _detect_risks(self, text: str) -> list[str]:
        risks = []
        if "数据" in text and not any(ch.isdigit() for ch in text):
            risks.append("任务涉及数据分析，但输入中缺少明确数值，需要人工补充或二次核验。")
        if "客户" in text or "用户" in text:
            risks.append("涉及客户或用户信息时，需要注意隐私脱敏和权限边界。")
        if "合同" in text or "财务" in text or "法务" in text:
            risks.append("涉及合同、财务或法务内容时，AI 结果只能作为辅助材料，需专业人员复核。")
        if not risks:
            risks.append("需避免无依据扩写，关键结论应与来源材料保持一致。")
        return risks

    def _recommendations(self, state: WorkflowState, risks: list[str]) -> list[str]:
        recs = [
            "优先沉淀标准模板，减少重复性材料编写成本。",
            "对高频任务建立固定 Agent 流程，降低人工沟通损耗。",
            "输出结果保留证据片段与审计日志，便于复核。",
        ]
        if risks:
            recs.append("对风险点设置人工确认节点，避免 AI 自动输出直接进入正式流程。")
        return recs
