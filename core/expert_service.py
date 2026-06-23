from langchain_deepseek import ChatDeepSeek

import settings
from models.expert import ExpertOrder, ExpertProfile


expert_llm = ChatDeepSeek(
    model=settings.DEEPSEEK_MODEL,
    api_key=settings.DEEPSEEK_API_KEY,
    temperature=0.4,
    timeout=120,
)


async def generate_expert_ai_draft(order: ExpertOrder, expert: ExpertProfile) -> str:
    prompt = f"""你是平台内部的专家辅助工具，请为真人专家准备一份分析初稿。初稿不能冒充最终人工报告。

专家方向：{expert.category} / {expert.title}
待分析名称：{order.selected_name}
用户需求：{order.requirements}

请从名称含义、传播记忆、文化语义、潜在风险和优化建议五个方面形成结构化中文初稿，并在结尾明确标注“本内容为 AI 初稿，须由专家人工审核修订后交付”。"""
    response = await expert_llm.ainvoke(prompt)
    return str(response.content)
