import json
import urllib.request
from typing import Any

from .settings import settings


class LLMClient:
    """Small OpenAI-compatible client with deterministic local fallback.

    The project must be runnable without paid APIs. When LLM_PROVIDER is set to
    `local-rule`, this client returns stable, template-based text. When set to
    `openai-compatible`, it calls /chat/completions using stdlib urllib.
    """

    def complete(self, system: str, user: str, temperature: float = 0.2) -> str:
        if settings.llm_provider != "openai-compatible" or not settings.openai_api_key:
            return self._local_answer(system, user)

        url = f"{settings.openai_base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": settings.openai_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.openai_api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except Exception as exc:  # pragma: no cover - network-dependent
            return self._local_answer(system, user) + f"\n\n> 真实模型调用失败，已自动降级：{exc}"

    def _local_answer(self, system: str, user: str) -> str:
        title = "自动化任务分析"
        if "周报" in user:
            title = "运营周报初稿"
        elif "会议纪要" in user:
            title = "会议纪要整理"
        elif "方案" in user:
            title = "执行方案初稿"
        return (
            f"## {title}\n\n"
            "### 一、任务判断\n"
            "该任务属于企业内部知识处理与经营分析辅助场景，适合采用多 Agent 分工处理。\n\n"
            "### 二、核心结论\n"
            "1. 需要先明确业务目标、资料来源、交付格式与风险边界。\n"
            "2. 需要将资料检索、结构化分析、内容生成和质量审核拆分处理，避免单次生成不可控。\n"
            "3. 输出结果应保留证据来源、审计记录和人工确认节点。\n\n"
            "### 三、建议动作\n"
            "- 建立标准模板，减少重复沟通成本。\n"
            "- 对高频任务沉淀任务类型和提示词模板。\n"
            "- 对关键结论增加来源引用和人工复核。\n"
        )


llm_client = LLMClient()
