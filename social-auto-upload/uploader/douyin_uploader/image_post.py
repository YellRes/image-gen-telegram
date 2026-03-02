# -*- coding: utf-8 -*-
import asyncio
from pathlib import Path
from typing import Iterable, List

from playwright.async_api import Playwright, Page, async_playwright

from conf import LOCAL_CHROME_HEADLESS, LOCAL_CHROME_PATH
from uploader.douyin_uploader.main import douyin_setup
from utils.base_social_media import set_init_script
from utils.log import douyin_logger


class DouYinImagePost(object):
    def __init__(self, title: str, image_paths: Iterable[str], tags: List[str], account_file: str):
        self.title = title or ""
        self.image_paths = [str(p) for p in image_paths if p]
        self.tags = tags or []
        self.account_file = str(account_file)
        self.local_executable_path = LOCAL_CHROME_PATH
        self.headless = LOCAL_CHROME_HEADLESS

    async def _open_image_publish_page(self, page: Page):
        await page.goto("https://creator.douyin.com/creator-micro/content/upload")
        await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload**")

        # 创作者中心有时会先落到视频页，优先切换到图文标签。
        image_tab = page.get_by_text("图文")
        if await image_tab.count():
            await image_tab.first.click()
            await asyncio.sleep(0.5)

    async def _upload_images(self, page: Page):
        if not self.image_paths:
            raise Exception("No image files found for Douyin image post")

        files = []
        for path in self.image_paths:
            if Path(path).exists():
                files.append(path)

        if not files:
            raise Exception("All image paths are missing")

        upload_input = page.locator("input[type='file']").first
        if not await upload_input.count():
            raise Exception("Douyin upload input not found")

        await upload_input.set_input_files(files)

        # 等待上传结束：出现发布按钮通常代表资源已就绪。
        for _ in range(90):
            publish_button = page.get_by_role("button", name="发布", exact=True)
            if await publish_button.count():
                return
            await asyncio.sleep(1)

        raise Exception("Douyin image upload timeout")

    async def _fill_title_and_tags(self, page: Page):
        if self.title:
            title_input = page.get_by_text("作品标题").locator("..").locator(
                "xpath=following-sibling::div[1]"
            ).locator("input")
            if await title_input.count():
                await title_input.fill(self.title[:30])
            else:
                # 图文标题区域在新版页面常是 contenteditable 容器。
                editor = page.locator(".notranslate").first
                if await editor.count():
                    await editor.click()
                    await page.keyboard.press("Control+KeyA")
                    await page.keyboard.press("Delete")
                    await page.keyboard.type(self.title[:200])
                    await page.keyboard.press("Enter")

        if self.tags:
            zone_selector = ".zone-container"
            if await page.locator(zone_selector).count():
                for tag in self.tags:
                    await page.type(zone_selector, f"#{tag}")
                    await page.press(zone_selector, "Space")
                douyin_logger.info(f"总共添加{len(self.tags)}个话题")

    async def _publish(self, page: Page):
        for _ in range(20):
            try:
                publish_button = page.get_by_role("button", name="发布", exact=True)
                if await publish_button.count():
                    await publish_button.first.click()
                await page.wait_for_url(
                    "https://creator.douyin.com/creator-micro/content/manage**",
                    timeout=5000,
                )
                return
            except Exception:
                douyin_logger.info("图文正在发布中...")
                await asyncio.sleep(1)

        raise Exception("Douyin image post failed or timeout")

    async def upload(self, playwright: Playwright):
        if self.local_executable_path:
            browser = await playwright.chromium.launch(
                headless=self.headless,
                executable_path=self.local_executable_path,
            )
        else:
            browser = await playwright.chromium.launch(headless=self.headless)

        context = await browser.new_context(storage_state=self.account_file)
        context = await set_init_script(context)
        page = await context.new_page()

        try:
            await self._open_image_publish_page(page)
            douyin_logger.info("[+] 正在上传抖音图文")
            await self._upload_images(page)
            await self._fill_title_and_tags(page)
            await self._publish(page)
            douyin_logger.success("[+] 抖音图文发布成功")
            await context.storage_state(path=self.account_file)
        finally:
            await context.close()
            await browser.close()

    async def main(self):
        async with async_playwright() as playwright:
            await self.upload(playwright)


async def douyin_image_setup(account_file, handle=False):
    return await douyin_setup(account_file, handle=handle)
