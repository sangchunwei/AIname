import base64
import html
from pathlib import Path
from uuid import uuid4

import httpx

import settings


class VisualProviderError(RuntimeError):
    pass


class MockVisualProvider:
    """用于本地打通完整流程的概念图提供器，不调用外部收费接口。"""

    name = "mock"
    palettes = [
        ("#2563eb", "#7c3aed"),
        ("#059669", "#0891b2"),
        ("#ea580c", "#db2777"),
        ("#111827", "#475569"),
    ]

    async def generate(self, *, prompt: str, count: int, asset_type: str, brand_name: str, slogan: str | None):
        output_dir = Path(settings.GENERATED_ASSET_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        files = []
        for index in range(count):
            first, second = self.palettes[index % len(self.palettes)]
            filename = f"{uuid4().hex}.svg"
            path = output_dir / filename
            safe_name = html.escape(brand_name)
            safe_slogan = html.escape(slogan or "让好名字成为品牌的开始")
            if asset_type == "business_card":
                svg = self._business_card_svg(safe_name, safe_slogan, first, second, index)
            else:
                svg = self._logo_svg(safe_name, first, second, index)
            path.write_text(svg, encoding="utf-8")
            files.append(f"{settings.PUBLIC_ASSET_PREFIX}/{filename}")
        return files

    @staticmethod
    def _logo_svg(name: str, first: str, second: str, index: int) -> str:
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{first}"/><stop offset="1" stop-color="{second}"/></linearGradient></defs>
<rect width="1024" height="1024" rx="80" fill="#f8fafc"/>
<g transform="translate(512 400) rotate({index * 15})"><circle r="178" fill="url(#g)"/><path d="M-95 30 L0-130 L95 30 L0 145 Z" fill="white" opacity=".92"/><circle r="48" fill="{first}"/></g>
<text x="512" y="700" text-anchor="middle" font-family="Arial,'Microsoft YaHei',sans-serif" font-size="86" font-weight="700" fill="#172033">{name}</text>
<text x="512" y="770" text-anchor="middle" font-family="Arial,'Microsoft YaHei',sans-serif" font-size="28" letter-spacing="8" fill="#64748b">BRAND CONCEPT {index + 1}</text>
</svg>'''

    @staticmethod
    def _business_card_svg(name: str, slogan: str, first: str, second: str, index: int) -> str:
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{first}"/><stop offset="1" stop-color="{second}"/></linearGradient><filter id="s"><feDropShadow dx="0" dy="20" stdDeviation="22" flood-opacity=".2"/></filter></defs>
<rect width="1400" height="900" fill="#eef2f7"/>
<g filter="url(#s)" transform="translate(150 190)"><rect width="1100" height="520" rx="28" fill="white"/><rect width="340" height="520" rx="28" fill="url(#g)"/><circle cx="170" cy="190" r="92" fill="white" opacity=".95"/><path d="M110 210 L170 105 L230 210 L170 285 Z" fill="{first}"/>
<text x="410" y="190" font-family="Arial,'Microsoft YaHei',sans-serif" font-size="78" font-weight="700" fill="#172033">{name}</text>
<text x="414" y="260" font-family="Arial,'Microsoft YaHei',sans-serif" font-size="30" fill="#64748b">{slogan}</text>
<line x1="414" y1="310" x2="980" y2="310" stroke="#e2e8f0" stroke-width="3"/>
<text x="414" y="375" font-family="Arial,sans-serif" font-size="24" fill="#475569">BRAND IDENTITY · CONCEPT {index + 1}</text>
<text x="414" y="425" font-family="Arial,sans-serif" font-size="22" fill="#94a3b8">hello@example.com   ·   www.example.com</text></g>
</svg>'''


class OpenAICompatibleVisualProvider:
    """适配返回 data[].b64_json 或 data[].url 的图像生成接口。"""

    name = "openai_compatible"

    async def generate(self, *, prompt: str, count: int, asset_type: str, brand_name: str, slogan: str | None):
        if not settings.IMAGE_API_URL or not settings.IMAGE_API_KEY:
            raise VisualProviderError("尚未配置图像生成 API 地址或密钥")

        payload = {
            "model": settings.IMAGE_MODEL,
            "prompt": prompt,
            "n": count,
            "size": settings.IMAGE_SIZE,
            "response_format": "b64_json",
        }
        headers = {"Authorization": f"Bearer {settings.IMAGE_API_KEY}"}
        async with httpx.AsyncClient(timeout=settings.IMAGE_API_TIMEOUT) as client:
            response = await client.post(settings.IMAGE_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            items = response.json().get("data", [])
            if not items:
                raise VisualProviderError("图像服务没有返回任何图片")

            output_dir = Path(settings.GENERATED_ASSET_DIR)
            output_dir.mkdir(parents=True, exist_ok=True)
            files = []
            for item in items:
                if item.get("b64_json"):
                    content = base64.b64decode(item["b64_json"])
                    suffix = ".png"
                elif item.get("url"):
                    image_response = await client.get(item["url"])
                    image_response.raise_for_status()
                    content = image_response.content
                    suffix = ".jpg" if "jpeg" in image_response.headers.get("content-type", "") else ".png"
                else:
                    continue
                filename = f"{uuid4().hex}{suffix}"
                (output_dir / filename).write_bytes(content)
                files.append(f"{settings.PUBLIC_ASSET_PREFIX}/{filename}")
        if not files:
            raise VisualProviderError("无法解析图像服务返回结果")
        return files


def get_visual_provider():
    if settings.IMAGE_PROVIDER == "mock":
        return MockVisualProvider()
    if settings.IMAGE_PROVIDER == "openai_compatible":
        return OpenAICompatibleVisualProvider()
    raise VisualProviderError(f"不支持的图像提供器：{settings.IMAGE_PROVIDER}")
