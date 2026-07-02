import base64
import json
from urllib.parse import urlencode

import httpx

import settings


ALIPAY_SANDBOX_GATEWAY = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"


def _key_lines(value: str) -> str:
    compact = "".join(value.replace("\\n", "\n").strip().splitlines())
    return "\n".join(compact[i:i + 64] for i in range(0, len(compact), 64))


def _private_key_candidates(value: str) -> list[bytes]:
    key = value.replace("\\n", "\n").strip()
    if "BEGIN" in key:
        return [key.encode("utf-8")]
    body = _key_lines(key)
    return [
        f"-----BEGIN PRIVATE KEY-----\n{body}\n-----END PRIVATE KEY-----".encode("utf-8"),
        f"-----BEGIN RSA PRIVATE KEY-----\n{body}\n-----END RSA PRIVATE KEY-----".encode("utf-8"),
    ]


def _normalize_public_key(value: str) -> bytes:
    key = value.replace("\\n", "\n").strip()
    if "BEGIN" not in key:
        key = f"-----BEGIN PUBLIC KEY-----\n{_key_lines(key)}\n-----END PUBLIC KEY-----"
    return key.encode("utf-8")


def _ordered_content(params: dict) -> str:
    items = []
    for key in sorted(params):
        if key == "sign":
            continue
        value = params[key]
        if value is None or value == "":
            continue
        items.append(f"{key}={value}")
    return "&".join(items)


def _crypto():
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ModuleNotFoundError as exc:
        raise RuntimeError("缺少 cryptography 依赖，请先安装 requirements.txt 后再使用支付宝沙箱支付") from exc
    return hashes, serialization, padding


def _sign(params: dict) -> str:
    hashes, serialization, padding = _crypto()
    last_error = None
    private_key = None
    for candidate in _private_key_candidates(settings.ALIPAY_PRIVATE_KEY):
        try:
            private_key = serialization.load_pem_private_key(candidate, password=None)
            break
        except ValueError as exc:
            last_error = exc
    if private_key is None:
        raise ValueError("支付宝应用私钥格式不正确，请使用 RSA/RSA2 应用私钥") from last_error
    signature = private_key.sign(
        _ordered_content(params).encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")


def verify_signature(params: dict) -> bool:
    hashes, serialization, padding = _crypto()
    sign = params.get("sign")
    if not sign:
        return False
    public_key = serialization.load_pem_public_key(_normalize_public_key(settings.ALIPAY_PUBLIC_KEY))
    try:
        public_key.verify(
            base64.b64decode(sign),
            _ordered_content(params).encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
    except Exception:
        return False
    return True


def amount_yuan(amount_cents: int) -> str:
    return f"{amount_cents / 100:.2f}"


def _base_request_params(method: str, biz_content: dict) -> dict:
    return {
        "app_id": settings.ALIPAY_APP_ID,
        "method": method,
        "format": "JSON",
        "charset": "utf-8",
        "sign_type": "RSA2",
        "timestamp": settings.now_string(),
        "version": "1.0",
        "biz_content": json.dumps(biz_content, ensure_ascii=False, separators=(",", ":")),
    }


def build_page_pay_url(*, out_trade_no: str, subject: str, amount_cents: int) -> str:
    biz_content = {
        "out_trade_no": out_trade_no,
        "product_code": "FAST_INSTANT_TRADE_PAY",
        "total_amount": amount_yuan(amount_cents),
        "subject": subject,
    }
    params = {
        **_base_request_params("alipay.trade.page.pay", biz_content),
        "notify_url": settings.ALIPAY_NOTIFY_URL,
        "return_url": settings.ALIPAY_RETURN_URL,
    }
    params["sign"] = _sign(params)
    return f"{ALIPAY_SANDBOX_GATEWAY}?{urlencode(params)}"


async def query_trade(out_trade_no: str) -> dict:
    params = _base_request_params("alipay.trade.query", {"out_trade_no": out_trade_no})
    params["sign"] = _sign(params)
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(ALIPAY_SANDBOX_GATEWAY, params=params)
    response.raise_for_status()
    payload = response.json()
    return payload.get("alipay_trade_query_response") or {}
