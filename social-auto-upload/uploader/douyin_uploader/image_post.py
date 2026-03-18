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
        await page.goto(
            "https://creator.douyin.com/creator-micro/content/upload",
            wait_until="domcontentloaded",
            timeout=90000,
        )
        await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload**", timeout=60000)

        # 创作者中心有时会先落到视频页，优先切换到图文标签。
        image_tab = page.get_by_text("发布图文")
        if await image_tab.count():
            await image_tab.first.click()
            await asyncio.sleep(0.5)

    async def _upload_images(self, page: Page):
        if not self.image_paths:
            raise Exception("No image files found for Douyin image post")

        files = []
        for path in self.image_paths:
            try:
                resolved = Path(path).expanduser().resolve(strict=True)
                if resolved.is_file():
                    files.append(str(resolved))
            except Exception:
                continue

        if not files:
            raise Exception(f"All image paths are missing or invalid: {self.image_paths}")

        upload_input = page.locator("div[class^='container-drag'] >> input[type='file'][accept*='image/']").first
        if not await upload_input.count():
            raise Exception("Douyin upload input not found")

        try:
            await page.wait_for_timeout(2000)
            # await upload_input.click()
            await upload_input.set_input_files(files)
            await page.wait_for_timeout(2000)
        except Exception as exc:
            raise Exception(f"Failed to set input files: {files}. error={exc}") from exc

        # 等待上传结束：出现发布按钮通常代表资源已就绪。
        for _ in range(90):
            publish_button = page.get_by_role("button", name="发布", exact=True)
            if await publish_button.count():
                return
            await asyncio.sleep(4)

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
                await asyncio.sleep(10)
                if await publish_button.count():
                    await publish_button.first.click()
                await page.wait_for_url(
                    "https://creator.douyin.com/creator-micro/content/manage**",
                    timeout=20000,
                )
                return
            except Exception:
                douyin_logger.info("图文正在发布中...")
                await asyncio.sleep(1)

        raise Exception("Douyin image post failed or timeout")
    
    # 快速搭建
    async def quick_setted(self, page: Page):
        """
        1. 查找页面中文本为 快速填写的 div, 找到后点击
        2. 等待页面出现 class=semi-modal-body 的 div
        3. 选择 class 开头包含 card-container 的第一个子元素 并点击
        4. 等待一秒钟 查找页面中 class 开发包含 footer-container 的 div , 再找到 div 中文本为 确定 的按钮  点击确定
        5. 等待 1s 
        """
        quick_fill = page.locator("div", has_text="快速填写").first
        if not await quick_fill.count():
            douyin_logger.info("未找到“快速填写”入口，跳过快速填写流程")
            return

        await quick_fill.click()

        modal_body = page.locator("div.semi-modal-body").first
        await modal_body.wait_for(state="visible", timeout=5000)

        first_card = modal_body.locator("div[class^='card-container']").first
        if not await first_card.count():
            raise Exception("快速填写弹窗中未找到卡片项: div[class^='card-container']")
        await first_card.click()

        await page.wait_for_timeout(1000)

        footer = page.locator("div[class^='footer-container']").first
        await footer.wait_for(state="visible", timeout=5000)
        confirm_button = footer.get_by_text("确定", exact=True).first
        if not await confirm_button.count():
            raise Exception("快速填写弹窗中未找到“确定”按钮")
        await confirm_button.click()

        await page.wait_for_timeout(1000)

    async def cover_setted(self, page: Page, timeout_seconds: int = 180):
        # 上传中会出现“取消上传”，当该提示消失时视为上传完成，可进行下一步。
        cancel_upload = page.get_by_text("取消上传")
        progress_container = page.locator("div[class^='container-info']")
        started = False
        for _ in range(timeout_seconds):
            if not started and await progress_container.count():
                started = True
            if started and not await cancel_upload.count():
                return
            await asyncio.sleep(1)
        raise Exception("Douyin image upload did not finish in time (cancel upload still visible)")

    async def douyin_checked(self, page: Page, timeout_seconds: int = 60):
        # 等待 class 前缀是 detectItemTitle 的 div 出现，视为通过抖音校验。
        checked_flag = page.locator("div[class^='detectItemTitle']")
        for _ in range(timeout_seconds):
            if await checked_flag.count():
                return
            await asyncio.sleep(1)
        raise Exception("Douyin content check marker not found in time")

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

            await page.wait_for_timeout(500)
            await self.cover_setted(page)
            await self.douyin_checked(page)
            # await self.quick_setted(page)
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
