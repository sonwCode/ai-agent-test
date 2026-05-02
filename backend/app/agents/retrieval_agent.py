from .base import BaseAgent, AgentResult, WorkflowState
from ..services.knowledge_service import knowledge_service


class KnowledgeRetrievalAgent(BaseAgent):
    name = "知识检索 Agent"
    step_name = "召回企业知识库证据"

    def run(self, state: WorkflowState) -> AgentResult:
        query = " ".join([state.title, state.goal, state.context, state.memory.get("intent", "")])
        results = knowledge_service.search(query, limit=8)
        state.evidence = results
        state.memory["evidence_count"] = len(results)
        evidence_lines = [f"- [{r['title']}#{r['chunk_index']}] score={r['score']}：{r['content'][:120]}" for r in results]
        summary = f"召回 {len(results)} 条知识片段。" if results else "知识库暂无强相关片段，进入无证据兜底生成。"
        return AgentResult(self.name, self.step_name, {"evidence": results, "preview": "\n".join(evidence_lines)}, summary)
