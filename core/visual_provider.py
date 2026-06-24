import base64
import html
import asyncio
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlparse

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
        async with httpx.AsyncClient(timeout=settings.IMAGE_API_TIMEOUT, trust_env=False) as client:
            try:
                response = await client.post(settings.IMAGE_API_URL, json=payload, headers=headers)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                body = exc.response.text[:500] if exc.response is not None else ""
                status_code = exc.response.status_code if exc.response is not None else "unknown"
                raise VisualProviderError(f"图像服务 HTTP {status_code}: {body}") from exc
            except httpx.RequestError as exc:
                raise VisualProviderError(f"图像服务请求失败: {type(exc).__name__}: {exc}") from exc
            try:
                response_data = response.json()
            except ValueError as exc:
                raise VisualProviderError(f"图像服务返回的不是 JSON: {response.text[:500]}") from exc
            items = response_data.get("data", [])
            if not items:
                raise VisualProviderError(f"图像服务没有返回任何图片: {str(response_data)[:500]}")

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


class DashScopeVisualProvider:
    """Aliyun DashScope/Model Studio text-to-image provider."""

    name = "dashscope"

    def _base_api_url(self) -> str:
        configured = settings.IMAGE_API_URL.strip()
        if not configured:
            return "https://dashscope.aliyuncs.com/api/v1"
        if "/api/v1/" in configured:
            return configured.split("/api/v1/", 1)[0].rstrip("/") + "/api/v1"
        parsed = urlparse(configured)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}/api/v1"
        return "https://dashscope.aliyuncs.com/api/v1"

    @staticmethod
    def _dashscope_size() -> str:
        return settings.IMAGE_SIZE.replace("x", "*")

    @staticmethod
    def _uses_legacy_protocol() -> bool:
        model = settings.IMAGE_MODEL.lower()
        legacy_prefixes = ("wanx2.", "wan2.0", "wan2.1", "wan2.2", "wan2.5")
        return model.startswith(legacy_prefixes)

    @staticmethod
    def _trim_prompt_for_model(prompt: str) -> str:
        model = settings.IMAGE_MODEL.lower()
        if model.startswith(("wanx2.1", "wan2.1", "wan2.2")):
            return prompt[:500]
        if model.startswith(("wan2.5",)):
            return prompt[:2000]
        return prompt[:2100]

    def _generation_endpoint(self) -> str:
        if self._uses_legacy_protocol():
            return f"{self._base_api_url()}/services/aigc/text2image/image-synthesis"
        return f"{self._base_api_url()}/services/aigc/image-generation/generation"

    def _payload(self, prompt: str, count: int) -> dict:
        clean_prompt = self._trim_prompt_for_model(prompt)
        parameters = {
            "size": self._dashscope_size(),
            "n": count,
            "watermark": False,
        }
        if self._uses_legacy_protocol():
            return {
                "model": settings.IMAGE_MODEL,
                "input": {"prompt": clean_prompt},
                "parameters": parameters,
            }

        parameters["prompt_extend"] = True
        return {
            "model": settings.IMAGE_MODEL,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": clean_prompt}],
                    }
                ]
            },
            "parameters": parameters,
        }

    async def _submit_task(self, client: httpx.AsyncClient, prompt: str, count: int) -> str:
        payload = self._payload(prompt, count)
        headers = {
            "Authorization": f"Bearer {settings.IMAGE_API_KEY}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }
        response = await client.post(
            self._generation_endpoint(),
            json=payload,
            headers=headers,
        )
        response_data = self._json_or_raise(response, "DashScope 创建任务")
        if response.status_code >= 400:
            raise VisualProviderError(self._error_text("DashScope 创建任务失败", response.status_code, response_data))
        task_id = (response_data.get("output") or {}).get("task_id")
        if not task_id:
            raise VisualProviderError(f"DashScope 没有返回 task_id: {str(response_data)[:500]}")
        return task_id

    async def _wait_task(self, client: httpx.AsyncClient, task_id: str) -> dict:
        headers = {"Authorization": f"Bearer {settings.IMAGE_API_KEY}"}
        max_attempts = max(1, int(settings.IMAGE_API_TIMEOUT // 2))
        last_payload = None
        for _ in range(max_attempts):
            response = await client.get(f"{self._base_api_url()}/tasks/{task_id}", headers=headers)
            response_data = self._json_or_raise(response, "DashScope 查询任务")
            last_payload = response_data
            if response.status_code >= 400:
                raise VisualProviderError(self._error_text("DashScope 查询任务失败", response.status_code, response_data))
            output = response_data.get("output") or {}
            status = output.get("task_status")
            if status == "SUCCEEDED":
                return response_data
            if status in {"FAILED", "UNKNOWN"}:
                raise VisualProviderError(self._error_text(f"DashScope 任务{status}", response.status_code, response_data))
            await asyncio.sleep(2)
        raise VisualProviderError(f"DashScope 任务超时: task_id={task_id}, last={str(last_payload)[:500]}")

    @staticmethod
    def _json_or_raise(response: httpx.Response, label: str) -> dict:
        try:
            return response.json()
        except ValueError as exc:
            raise VisualProviderError(f"{label}返回的不是 JSON: HTTP {response.status_code}: {response.text[:500]}") from exc

    @staticmethod
    def _error_text(prefix: str, status_code: int, payload: dict) -> str:
        code = payload.get("code") or ""
        message = payload.get("message") or ""
        return f"{prefix}: HTTP {status_code} {code} {message} {str(payload)[:500]}"

    @staticmethod
    def _extract_image_urls(payload: dict) -> list[str]:
        urls = []
        output = payload.get("output") or {}
        results = output.get("results") or []
        for item in results:
            image_url = item.get("url")
            if image_url:
                urls.append(image_url)

        choices = output.get("choices") or []
        for choice in choices:
            content = (((choice.get("message") or {}).get("content")) or [])
            for item in content:
                image_url = item.get("image")
                if image_url:
                    urls.append(image_url)
        return urls

    async def generate(self, *, prompt: str, count: int, asset_type: str, brand_name: str, slogan: str | None):
        if not settings.IMAGE_API_KEY:
            raise VisualProviderError("尚未配置 DashScope API Key")

        output_dir = Path(settings.GENERATED_ASSET_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        async with httpx.AsyncClient(timeout=settings.IMAGE_API_TIMEOUT, trust_env=False) as client:
            try:
                task_id = await self._submit_task(client, prompt, count)
                result_payload = await self._wait_task(client, task_id)
            except httpx.RequestError as exc:
                raise VisualProviderError(f"DashScope 请求失败: {type(exc).__name__}: {exc}") from exc

            image_urls = self._extract_image_urls(result_payload)
            if not image_urls:
                raise VisualProviderError(f"DashScope 任务成功但没有图片 URL: {str(result_payload)[:500]}")

            files = []
            for image_url in image_urls:
                try:
                    image_response = await client.get(image_url)
                    image_response.raise_for_status()
                except httpx.RequestError as exc:
                    raise VisualProviderError(
                        f"DashScope 图片下载失败: {type(exc).__name__}: {exc}; url={image_url[:160]}"
                    ) from exc
                except httpx.HTTPStatusError as exc:
                    status_code = exc.response.status_code if exc.response is not None else "unknown"
                    raise VisualProviderError(
                        f"DashScope 图片下载 HTTP {status_code}: url={image_url[:160]}"
                    ) from exc
                content_type = image_response.headers.get("content-type", "")
                suffix = ".jpg" if "jpeg" in content_type else ".png"
                filename = f"{uuid4().hex}{suffix}"
                (output_dir / filename).write_bytes(image_response.content)
                files.append(f"{settings.PUBLIC_ASSET_PREFIX}/{filename}")
        return files


def get_visual_provider():
    if settings.IMAGE_PROVIDER == "mock":
        return MockVisualProvider()
    if settings.IMAGE_PROVIDER in {"dashscope", "aliyun_dashscope"} or "dashscope.aliyuncs.com" in settings.IMAGE_API_URL:
        return DashScopeVisualProvider()
    if settings.IMAGE_PROVIDER == "openai_compatible":
        return OpenAICompatibleVisualProvider()
    raise VisualProviderError(f"不支持的图像提供器：{settings.IMAGE_PROVIDER}")
