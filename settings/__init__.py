"""项目统一配置入口，优先读取操作系统环境变量，其次读取本地 .env。"""
import os
from datetime import timedelta
from pathlib import Path


def _load_local_env() -> None:
    """加载项目根目录的 .env，不覆盖操作系统中已经存在的同名变量。"""
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)


_load_local_env()


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or not value.strip() or "REPLACE_ME" in value:
        raise RuntimeError(f"缺少必要配置：{name}，请填写项目根目录的 .env 文件")
    return value.strip()


# 数据库与基础设施
DB_URI = _env("AINAME_MYSQL_DB_URI")
POSTGRES_CHECKPOINT_DB_URI = _env("AINAME_POSTGRES_CHECKPOINT_DB_URI")
REDIS_URL = os.getenv("AINAME_REDIS_URL", "redis://127.0.0.1:6379/0")
OLLAMA_BASE_URL = os.getenv("AINAME_OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip()
OLLAMA_EMBED_MODEL = os.getenv("AINAME_OLLAMA_EMBED_MODEL", "nomic-embed-text").strip()

# 大模型
DEEPSEEK_API_KEY = _env("AINAME_DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.getenv("AINAME_DEEPSEEK_MODEL", "deepseek-chat")

# 邮箱
MAIL_USERNAME = _env("AINAME_MAIL_USERNAME")
MAIL_PASSWORD = _env("AINAME_MAIL_PASSWORD")
MAIL_FROM = os.getenv("AINAME_MAIL_FROM", MAIL_USERNAME)
MAIL_PORT = int(os.getenv("AINAME_MAIL_PORT", "587"))
MAIL_SERVER = os.getenv("AINAME_MAIL_SERVER", "smtp.qq.com")
MAIL_FROM_NAME = os.getenv("AINAME_MAIL_FROM_NAME", "ainameapp")
MAIL_STARTTLS = os.getenv("AINAME_MAIL_STARTTLS", "true").lower() == "true"
MAIL_SSL_TLS = os.getenv("AINAME_MAIL_SSL_TLS", "false").lower() == "true"

# JWT
JWT_SECRET_KEY = _env("AINAME_JWT_SECRET_KEY")
JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=int(os.getenv("AINAME_JWT_ACCESS_DAYS", "1")))
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv("AINAME_JWT_REFRESH_DAYS", "30")))

# 品牌视觉生成。默认 mock 可直接打通流程；生产环境可切换兼容图像 API。
PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_PROVIDER = os.getenv("AINAME_IMAGE_PROVIDER", "mock").strip().lower()
IMAGE_API_URL = os.getenv("AINAME_IMAGE_API_URL", "").strip()
IMAGE_API_KEY = os.getenv("AINAME_IMAGE_API_KEY", "").strip()
IMAGE_MODEL = os.getenv("AINAME_IMAGE_MODEL", "image-generation-model").strip()
IMAGE_SIZE = os.getenv("AINAME_IMAGE_SIZE", "1024x1024").strip()
IMAGE_API_TIMEOUT = float(os.getenv("AINAME_IMAGE_API_TIMEOUT", "180"))
GENERATED_ASSET_DIR = os.getenv("AINAME_GENERATED_ASSET_DIR", str(PROJECT_ROOT / "generated"))
PUBLIC_ASSET_PREFIX = "/generated"
DEFAULT_AVATAR_DIR = PROJECT_ROOT / "static" / "default-avatars"
DEFAULT_AVATAR_PREFIX = "/default-avatars"

# 仅限本地开发的模拟支付；生产环境必须保持 false。
MOCK_PAYMENT_ENABLED = os.getenv("AINAME_MOCK_PAYMENT_ENABLED", "false").lower() == "true"
FREE_DAILY_NAME_LIMIT = int(os.getenv("AINAME_FREE_DAILY_NAME_LIMIT", "10"))
FREE_DAILY_VISUAL_LIMIT = int(os.getenv("AINAME_FREE_DAILY_VISUAL_LIMIT", "2"))

# 本地增长与模拟资金配置
EXPERT_PLATFORM_FEE_BPS = int(os.getenv("AINAME_EXPERT_PLATFORM_FEE_BPS", "1000"))
INVITER_REWARD_CREDITS = int(os.getenv("AINAME_INVITER_REWARD_CREDITS", "3"))
INVITEE_REWARD_CREDITS = int(os.getenv("AINAME_INVITEE_REWARD_CREDITS", "1"))
DEFAULT_PARTNER_COMMISSION_BPS = int(os.getenv("AINAME_DEFAULT_PARTNER_COMMISSION_BPS", "1000"))
PUBLIC_H5_URL = os.getenv("AINAME_PUBLIC_H5_URL", "http://127.0.0.1:8080").rstrip("/")
