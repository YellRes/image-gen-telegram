# Progress Compact

## Done
- Added Douyin image post uploader at `social-auto-upload/uploader/douyin_uploader/image_post.py`.
- Added `social-auto-upload/conf.py` so existing uploader modules can import runtime config.
- Added root adapter `douyin_image_publish.py` to bridge Telegram bot and social-auto-upload uploader.
- Wired Telegram flow in `telegram_bot.py` with env-gated auto publish.
- Added verification script `verify_douyin_image_publish.py`.
- Updated `.env.example`, `requirements.txt`, and `README.md` with setup and Windows usage.

## New Runtime Flags
- `ENABLE_DOUYIN_IMAGE_PUBLISH`
- `DOUYIN_ACCOUNT_FILE`
- `DOUYIN_LOGIN_INTERACTIVE`
- `DOUYIN_PUBLISH_TAGS`

## Notes
- Auto publish is optional and non-blocking to image generation success path.
- If Douyin cookie is missing/expired and interactive login is disabled, publish fails with clear error.

## 2026-03-02 Compatibility Fix
- Updated `text_to_image.py` to support both Minimax response formats:
  - old: `data[0].base64`
  - new: `data.image_urls[0]`
- When `output_path` is provided and response contains URL, image is downloaded and saved locally.
- This unblocks Telegram -> Playwright Douyin flow when Minimax no longer returns base64.

## 2026-03-05 Post-generate Publish Orchestration
- Added async orchestrator `generate_and_publish_to_douyin(...)` in `text_to_image.py`.
- Orchestrator supports both:
  - generate-then-publish (via `output_path`)
  - publish-existing-images (via `image_paths`)
- Unified Telegram publish call path in `telegram_bot.py` to use orchestrator result status.
- Hardened publish failure handling:
  - keep generation success path
  - return/propagate publish status and error message cleanly for user notification.
