"""
Adapter for publishing generated images to Douyin via Playwright.
"""

import os
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional


SOCIAL_UPLOAD_DIR = Path(__file__).parent / "social-auto-upload"
if str(SOCIAL_UPLOAD_DIR) not in sys.path:
    sys.path.insert(0, str(SOCIAL_UPLOAD_DIR))

try:
    from uploader.douyin_uploader.image_post import DouYinImagePost, douyin_image_setup
except Exception as exc:  # pragma: no cover - import error only appears in runtime environment.
    DouYinImagePost = None
    douyin_image_setup = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


def build_douyin_tags(prompt: str, extra_tags: Optional[Iterable[str]] = None) -> List[str]:
    tags = []
    if extra_tags:
        tags.extend([str(tag).strip() for tag in extra_tags if str(tag).strip()])

    words = re.findall(r"[\u4e00-\u9fffA-Za-z0-9_]{2,20}", prompt or "")
    tags.extend(words[:5])

    seen = set()
    normalized = []
    for item in tags:
        if item not in seen:
            seen.add(item)
            normalized.append(item)
    return normalized[:8]


async def publish_images_to_douyin(
    title: str,
    image_paths: Iterable[str],
    tags: Optional[Iterable[str]] = None,
    account_file: Optional[str] = None,
    handle_login: bool = False,
) -> str:
    """
    Publish generated images to Douyin creator center.
    Returns a short status message on success/failure.
    """
    if IMPORT_ERROR or DouYinImagePost is None or douyin_image_setup is None:
        raise RuntimeError(
            f"Douyin publisher import failed: {IMPORT_ERROR}. "
            "Please install dependencies and ensure social-auto-upload/conf.py exists."
        )

    default_account = SOCIAL_UPLOAD_DIR / "cookies" / "douyin_uploader" / "account.json"
    account_path = Path(account_file) if account_file else default_account
    account_path.parent.mkdir(parents=True, exist_ok=True)

    ok = await douyin_image_setup(str(account_path), handle=handle_login)
    if not ok:
        raise RuntimeError(
            "Douyin cookie is invalid or missing. "
            "Run login flow first or enable interactive login."
        )

    file_list = [str(Path(p)) for p in image_paths if p and Path(p).exists()]
    if not file_list:
        raise RuntimeError("No valid image files to publish")

    tag_list = build_douyin_tags(title, tags)
    app = DouYinImagePost(
        title=title,
        image_paths=file_list,
        tags=tag_list,
        account_file=str(account_path),
    )
    await app.main()
    return "ok"


def parse_env_tags(raw: str) -> List[str]:
    if not raw:
        return []
    splitters = [",", "，", " "]
    result = [raw]
    for splitter in splitters:
        next_result = []
        for part in result:
            next_result.extend(part.split(splitter))
        result = next_result
    return [item.strip() for item in result if item.strip()]


def is_douyin_publish_enabled() -> bool:
    return os.getenv("ENABLE_DOUYIN_IMAGE_PUBLISH", "false").strip().lower() in {"1", "true", "yes", "on"}


if __name__ == '__main__':
    import asyncio
    # path 示例（任选一种写法）：
    # 相对路径（相对当前工作目录）:
    #   image_paths = ["images/pic.jpg"]
    # Windows 绝对路径用正斜杠或 raw 字符串:
    #   image_paths = [r"d:\python-playground\telegram-image-gen\images\pic.jpg"]
    #   image_paths = ["d:/python-playground/telegram-image-gen/images/pic.jpg"]
    image_paths = [str(Path(__file__).parent / "images" / "2026" / "03" / "15" / "8214821709_2c8aff1f14f0_1_193648288904.jpeg")]  # 改成实际存在的图片路径
    # 首次运行建议开启 handle_login=True，会拉起浏览器登录并保存 cookie。
    asyncio.run(publish_images_to_douyin("test", image_paths, handle_login=True))
