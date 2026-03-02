"""
Minimal verification script for Douyin image publishing.

Usage (Windows PowerShell):
python verify_douyin_image_publish.py --title "测试图文" --images temp\\a.jpeg temp\\b.jpeg --tags AI 自动化
"""

import argparse
import asyncio

from douyin_image_publish import publish_images_to_douyin


def build_args():
    parser = argparse.ArgumentParser(description="Verify Douyin image publish flow")
    parser.add_argument("--title", required=True, help="Post title")
    parser.add_argument("--images", nargs="+", required=True, help="Image file paths")
    parser.add_argument("--tags", nargs="*", default=[], help="Optional tags")
    parser.add_argument("--account-file", default="", help="Optional cookie file path")
    parser.add_argument(
        "--interactive-login",
        action="store_true",
        help="Enable Playwright interactive login when cookie is invalid",
    )
    return parser.parse_args()


async def main():
    args = build_args()
    await publish_images_to_douyin(
        title=args.title,
        image_paths=args.images,
        tags=args.tags,
        account_file=args.account_file or None,
        handle_login=args.interactive_login,
    )
    print("Douyin image publish flow completed.")


if __name__ == "__main__":
    asyncio.run(main())
