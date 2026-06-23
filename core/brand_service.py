from langchain_deepseek import ChatDeepSeek

import settings
from models.brand import BrandProject
from schemas.brand_schemas import BrandStrategyResult


strategy_llm = ChatDeepSeek(
    model=settings.DEEPSEEK_MODEL,
    api_key=settings.DEEPSEEK_API_KEY,
    temperature=0.6,
    timeout=120,
).with_structured_output(BrandStrategyResult).with_retry(stop_after_attempt=3)


async def generate_brand_strategy(project: BrandProject) -> BrandStrategyResult:
    prompt = f"""你是一位品牌策略与视觉创意总监，请为以下品牌生成可直接用于视觉设计的品牌策略。

品牌名称：{project.selected_name}
名称寓意：{project.name_moral or '未提供'}
名称出处：{project.name_reference or '未提供'}
所属行业：{project.industry}
目标用户：{project.audience or '大众用户'}
期望风格：{project.style}
颜色偏好：{project.color_preference or '由你根据品牌定位推荐'}

请输出：
1. 一段简洁、有区分度的品牌定位摘要；
2. 3 到 8 个适合 Logo 生成的视觉关键词；
3. 3 到 5 条简短、原创、易传播的中文 Slogan，并解释每条的创意逻辑。
避免模仿或直接引用已知品牌口号。"""
    return await strategy_llm.ainvoke(prompt)


def build_visual_prompt(project: BrandProject, asset_type: str, slogan: str | None = None) -> str:
    keywords = project.visual_keywords or project.style
    base = (
        f"Brand name: {project.selected_name}. Industry: {project.industry}. "
        f"Brand positioning: {project.brand_brief or project.name_moral or ''}. "
        f"Visual keywords: {keywords}. Preferred colors: {project.color_preference or 'professionally balanced palette'}. "
    )
    if asset_type == "business_card":
        return base + (
            f"Create a premium business card mockup, front and back layout, slogan: {slogan or 'none'}, "
            "clean typography area, realistic stationery presentation, high-end brand identity, no watermark."
        )
    return base + (
        "Create a distinctive minimalist logo concept and brand symbol, centered composition, flat vector-like design, "
        "simple geometry, scalable silhouette, plain background, no mockup, no watermark, avoid unreadable text."
    )
