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

## 2026-03-05 Runtime Dependency/Login Fix
- Installed missing runtime dependency `loguru` in project venv.
- Added `loguru>=0.7.3` into `requirements.txt` to avoid repeat import errors.
- Updated `douyin_image_publish.py` local entry to call:
  - `publish_images_to_douyin(..., handle_login=True)`
- This enables first-run interactive Douyin login and cookie persistence.

## 2026-03-05 Path Upload Hardening
- Hardened Douyin image uploader path handling in `image_post.py`.
- Upload paths now use `Path(...).expanduser().resolve(strict=True)` and must be real files.
- Added explicit error details when `set_input_files` fails, including resolved file list.

## 2026-03-05 Upload Format Compatibility
- Added image normalization before Douyin upload.
- Non-JPEG images (e.g. PNG/WebP) are now converted to JPEG into `cookies/douyin_uploader/upload_cache`.
- This mitigates Douyin UI error: "暂不支持这个格式".

## 2026-03-05 Douyin Upload State Checks
- Implemented `cover_setted(self, page)`:
  - waits for upload progress to start via `container-info*`
  - then waits until "取消上传" disappears
- Implemented `douyin_checked(self, page)`:
  - waits for `div[class^='detectItemTitle']` as validation marker
- Fixed method calls in `upload()` to pass `page` explicitly.

## 2026-03-10 OpenRouter Image Migration
- Replaced Minimax image generation in `text_to_image.py` with OpenRouter chat completions API:
  - endpoint: `https://openrouter.ai/api/v1/chat/completions`
  - auth env: `OPEN_ROUTER_KEY`
  - default model: `google/gemini-3-flash-preview`
- Added robust OpenRouter image extraction to support:
  - `message.images[*]`
  - `message.content[*].image_url`
  - data URL base64 and plain image URL in text payloads
- Updated `telegram_bot.py` config checks/messages to OpenRouter key naming.
- Updated `.env.example`, `README.md`, and `example.py` to OpenRouter variables and usage examples.

## 2026-03-10 Local Archive By Date
- Implemented local archive path builder in `telegram_bot.py`:
  - output path format: `images/YYYY/MM/DD/<userId>_<promptHash>_<index>_<timestamp>.jpeg`
  - date folders are created by existing `text_to_image.py` parent-dir `mkdir(...)` logic
- Replaced old Telegram temp output path (`temp/...jpeg`) with archive path builder.
- Removed Telegram post-send cleanup (`os.remove(...)`) so generated files are retained locally.
- Updated `README.md` to document date-based archive directory and keep-files behavior.

## 2026-03-10 Fixed Comic Explain Prompt (Chinese)
- Added fixed template `COMIC_EXPLAIN_ZH_TEMPLATE` in `prompt_manager.py` for "comic explanation of input text".
- Added `PromptBuilder.build_comic_explain_prompt(...)` and wired `style="comic"` to use the fixed template.
- Updated `text_to_image.py` CLI default behavior:
  - by default transforms input text via comic explain template (Chinese text requirement included)
  - added `--raw-prompt` to bypass template and send original prompt directly.
