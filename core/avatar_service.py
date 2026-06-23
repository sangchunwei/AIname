from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError

import settings


MAX_AVATAR_BYTES = 5 * 1024 * 1024
AVATAR_SIZE = 512
MAX_AVATAR_PIXELS = 25_000_000
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
DEFAULT_AVATARS = [
    {"key": "panda", "name": "团团熊猫", "url": f"{settings.DEFAULT_AVATAR_PREFIX}/panda.svg"},
    {"key": "cat", "name": "橘子猫咪", "url": f"{settings.DEFAULT_AVATAR_PREFIX}/cat.svg"},
    {"key": "bunny", "name": "草莓兔兔", "url": f"{settings.DEFAULT_AVATAR_PREFIX}/bunny.svg"},
    {"key": "bear", "name": "焦糖小熊", "url": f"{settings.DEFAULT_AVATAR_PREFIX}/bear.svg"},
    {"key": "fox", "name": "元气狐狸", "url": f"{settings.DEFAULT_AVATAR_PREFIX}/fox.svg"},
    {"key": "chick", "name": "太阳小鸡", "url": f"{settings.DEFAULT_AVATAR_PREFIX}/chick.svg"},
]


class AvatarValidationError(ValueError):
    pass


def get_default_avatar(avatar_key: str) -> dict[str, str] | None:
    return next((avatar for avatar in DEFAULT_AVATARS if avatar["key"] == avatar_key), None)


def _prepare_avatar(content: bytes) -> Image.Image:
    try:
        with Image.open(BytesIO(content)) as source:
            if source.format not in ALLOWED_FORMATS:
                raise AvatarValidationError("仅支持 JPEG、PNG 和 WebP 图片")
            if source.width * source.height > MAX_AVATAR_PIXELS:
                raise AvatarValidationError("图片分辨率过高，请选择较小的图片")
            source.verify()

        with Image.open(BytesIO(content)) as source:
            image = ImageOps.exif_transpose(source)
            image.load()
            width, height = image.size
            if width < 1 or height < 1:
                raise AvatarValidationError("图片尺寸无效")

            side = min(width, height)
            left = (width - side) // 2
            top = (height - side) // 2
            image = image.crop((left, top, left + side, top + side))
            image = image.resize((AVATAR_SIZE, AVATAR_SIZE), Image.Resampling.LANCZOS)

            if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
                rgba = image.convert("RGBA")
                background = Image.new("RGB", rgba.size, "white")
                background.paste(rgba, mask=rgba.getchannel("A"))
                return background
            return image.convert("RGB")
    except AvatarValidationError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise AvatarValidationError("图片文件无效或已损坏") from exc


def save_avatar(content: bytes, user_id: int) -> tuple[str, Path]:
    if not content:
        raise AvatarValidationError("头像文件不能为空")
    if len(content) > MAX_AVATAR_BYTES:
        raise AvatarValidationError("头像文件不能超过 5 MB")

    image = _prepare_avatar(content)
    avatar_dir = Path(settings.GENERATED_ASSET_DIR) / "avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{user_id}_{uuid4().hex}.jpg"
    final_path = avatar_dir / filename
    temp_path = avatar_dir / f".{filename}.tmp"
    try:
        image.save(temp_path, format="JPEG", quality=88, optimize=True, progressive=True)
        temp_path.replace(final_path)
    finally:
        image.close()
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)

    return f"{settings.PUBLIC_ASSET_PREFIX}/avatars/{filename}", final_path


def delete_local_avatar(avatar_url: str | None) -> None:
    if not avatar_url:
        return
    expected_prefix = f"{settings.PUBLIC_ASSET_PREFIX}/avatars/"
    if not avatar_url.startswith(expected_prefix):
        return
    avatar_dir = (Path(settings.GENERATED_ASSET_DIR) / "avatars").resolve()
    path = (avatar_dir / Path(avatar_url).name).resolve()
    if path.parent == avatar_dir and path.suffix.lower() == ".jpg":
        path.unlink(missing_ok=True)
