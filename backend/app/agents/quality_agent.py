from .base import BaseAgent, AgentResult, WorkflowState


class QualityReviewAgent(BaseAgent):
    name = "质量审核 Agent"
    step_name = "质量评分与风险复核"

    def run(self, state: WorkflowState) -> AgentResult:
        content = state.final_content
        checks = []
        score = 50.0

        if len(content) >= 800:
            score += 12
            checks.append({"item": "内容完整度", "passed": True, "detail": "正文长度满足基础交付要求"})
        else:
            checks.append({"item": "内容完整度", "passed": False, "detail": "正文偏短"})

        if state.evidence:
            score += 18
            checks.append({"item": "证据支撑", "passed": True, "detail": f"包含 {len(state.evidence)} 条知识库证据"})
        else:
            checks.append({"item": "证据支撑", "passed": False, "detail": "缺少知识库证据，需人工补充"})

        required_headers = ["任务背景", "关键要点", "风险", "后续建议"]
        header_hits = sum(1 for h in required_headers if h in content)
        score += header_hits * 4
        checks.append({"item": "格式规范", "passed": header_hits >= 3, "detail": f"命中 {header_hits}/{len(required_headers)} 个核心章节"})

        if "人工确认" in content or "待确认" in content:
            score += 8
            checks.append({"item": "人工复核", "passed": True, "detail": "包含人工确认节点"})
        else:
            checks.append({"item": "人工复核", "passed": False, "detail": "缺少人工确认节点"})

        score = min(round(score, 1), 100.0)
        state.quality_score = score
        state.memory["quality_checks"] = checks
        status = "success" if score >= 70 else "warning"
        summary = f"质量评分 {score} 分，{'达到演示验收标准' if score >= 70 else '建议补充资料后重跑'}。"
        return AgentResult(self.name, self.step_name, {"score": score, "checks": checks}, summary, status=status)
