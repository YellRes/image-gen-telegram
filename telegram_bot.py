"""
Telegram Bot for Image Generation
Receives messages from Telegram and generates images using OpenRouter API
"""

import os
import logging
import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Import our text to image module
from text_to_image import text_to_image, generate_and_publish_to_douyin
from douyin_image_publish import (
    is_douyin_publish_enabled,
    parse_env_tags,
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()

# Environment variables
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
OPEN_ROUTER_KEY = os.getenv("OPEN_ROUTER_KEY", "")
PROXY_URL = os.getenv("PROXY_URL", "")
ENABLE_DOUYIN_IMAGE_PUBLISH = is_douyin_publish_enabled()
DOUYIN_ACCOUNT_FILE = os.getenv("DOUYIN_ACCOUNT_FILE", "")
DOUYIN_LOGIN_INTERACTIVE = os.getenv("DOUYIN_LOGIN_INTERACTIVE", "false").strip().lower() in {"1", "true", "yes", "on"}
DOUYIN_EXTRA_TAGS = parse_env_tags(os.getenv("DOUYIN_PUBLISH_TAGS", ""))

from prompt_manager import QUALITY_PRESETS, DEFAULT_QUALITY, STYLE_PRESETS, DEFAULT_STYLE, prompt_builder
DEFAULT_IMAGE_COUNT = 1
MAX_IMAGE_COUNT = 4

# States for conversation
(
    WAITING_FOR_PROMPT,
    WAITING_FOR_SIZE,
) = range(2)


def _build_archive_output_path(user_id: int, prompt: str, index: int) -> str:
    """Build archive path: images/YYYY/MM/DD/<unique-name>.jpeg."""
    now = datetime.now()
    date_dir = Path("images") / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d")
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
    timestamp = now.strftime("%H%M%S%f")
    filename = f"{user_id}_{prompt_hash}_{index}_{timestamp}.jpeg"
    return str(date_dir / filename)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "🎨 Welcome to Image Generator Bot!\n\n"
        "Send me a text description and I'll generate an image for you.\n\n"
        "Commands:\n"
        "/start - Show this message\n"
        "/help - Show help\n"
        "/status - Check configuration status\n"
        "/quality - Show current quality\n"
        "/quality low|medium|high - Set quality\n"
        "/style - Show current style\n"
        "/style default|comic - Set style\n"
        "/count - Show current image count\n"
        f"/count 1-{MAX_IMAGE_COUNT} - Set image count"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "📖 How to use:\n\n"
        "1. Send me any text description\n"
        "2. I'll generate an image using AI\n"
        "3. You'll receive the generated image\n\n"
        "Example: 'A cute cat sitting on a sofa'\n\n"
        "Quality control:\n"
        "/quality low|medium|high\n\n"
        "Style control:\n"
        "/style default|comic\n\n"
        "Image count control:\n"
        f"/count 1-{MAX_IMAGE_COUNT}\n\n"
        "Note: Make sure the bot is properly configured with API keys."
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check bot configuration status"""
    status = []
    status.append("🔧 Configuration Status:\n")
    
    if TG_BOT_TOKEN:
        status.append("✅ Telegram Bot Token: Configured")
    else:
        status.append("❌ Telegram Bot Token: NOT SET (TG_BOT_TOKEN)")
    
    if OPEN_ROUTER_KEY:
        status.append("✅ OpenRouter API Key: Configured")
    else:
        status.append("❌ OpenRouter API Key: NOT SET (OPEN_ROUTER_KEY)")

    quality = context.user_data.get("quality", DEFAULT_QUALITY)
    quality_label = QUALITY_PRESETS.get(quality, QUALITY_PRESETS[DEFAULT_QUALITY])["label"]
    status.append(f"🎛️ Current Quality: {quality} ({quality_label})")
    
    style = context.user_data.get("style", DEFAULT_STYLE)
    style_label = STYLE_PRESETS.get(style, STYLE_PRESETS[DEFAULT_STYLE])["label"]
    status.append(f"🎨 Current Style: {style} ({style_label})")
    
    image_count = context.user_data.get("image_count", DEFAULT_IMAGE_COUNT)
    status.append(f"🖼️ Current Image Count: {image_count}")
    status.append(f"📤 Douyin Auto Publish: {'ON' if ENABLE_DOUYIN_IMAGE_PUBLISH else 'OFF'}")
    
    await update.message.reply_text("\n".join(status))


async def quality_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get or set image quality profile."""
    args = context.args

    if not args:
        current = context.user_data.get("quality", DEFAULT_QUALITY)
        current_label = QUALITY_PRESETS[current]["label"]
        await update.message.reply_text(
            "🎛️ 当前图片质量设置:\n"
            f"- {current} ({current_label})\n\n"
            "可用档位:\n"
            "- low: 低质量(更快)\n"
            "- medium: 中质量(平衡)\n"
            "- high: 高质量(更慢)\n\n"
            "使用方式: /quality low|medium|high"
        )
        return

    level = args[0].strip().lower()
    alias = {
        "低": "low",
        "中": "medium",
        "高": "high",
    }
    level = alias.get(level, level)

    if level not in QUALITY_PRESETS:
        await update.message.reply_text(
            "❌ 无效档位。请使用: /quality low|medium|high"
        )
        return

    context.user_data["quality"] = level
    await update.message.reply_text(
        f"✅ 已切换质量到: {level} ({QUALITY_PRESETS[level]['label']})"
    )


async def style_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get or set image style profile."""
    args = context.args

    if not args:
        current = context.user_data.get("style", DEFAULT_STYLE)
        current_label = STYLE_PRESETS.get(current, STYLE_PRESETS[DEFAULT_STYLE])["label"]
        
        style_options = []
        for k, v in STYLE_PRESETS.items():
            style_options.append(f"- {k}: {v['label']}")
        
        options_text = "\n".join(style_options)
            
        await update.message.reply_text(
            "🎨 当前图片风格设置:\n"
            f"- {current} ({current_label})\n\n"
            "可用风格:\n"
            f"{options_text}\n\n"
            "使用方式: /style default|comic"
        )
        return

    level = args[0].strip().lower()

    if level not in STYLE_PRESETS:
        await update.message.reply_text(
            "❌ 无效风格。请使用: /style default|comic"
        )
        return

    context.user_data["style"] = level
    await update.message.reply_text(
        f"✅ 已切换风格到: {level} ({STYLE_PRESETS[level]['label']})"
    )


async def count_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get or set number of generated images."""
    args = context.args

    if not args:
        current = context.user_data.get("image_count", DEFAULT_IMAGE_COUNT)
        await update.message.reply_text(
            "🖼️ 当前生成数量设置:\n"
            f"- {current} 张/次\n\n"
            f"使用方式: /count 1-{MAX_IMAGE_COUNT}"
        )
        return

    try:
        count = int(args[0].strip())
    except ValueError:
        await update.message.reply_text(
            f"❌ 数量必须是数字。请使用: /count 1-{MAX_IMAGE_COUNT}"
        )
        return

    if count < 1 or count > MAX_IMAGE_COUNT:
        await update.message.reply_text(
            f"❌ 数量超出范围。请使用: /count 1-{MAX_IMAGE_COUNT}"
        )
        return

    context.user_data["image_count"] = count
    await update.message.reply_text(f"✅ 已设置生成数量为: {count} 张/次")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages"""
    user = update.effective_user
    prompt = update.message.text
    
    logger.info(f"Received prompt from {user.name}: {prompt}")
    
    # Check if API keys are configured
    if not OPEN_ROUTER_KEY:
        await update.message.reply_text(
            "❌ Bot is not properly configured. Please set OPEN_ROUTER_KEY environment variable."
        )
        return
    
    quality = context.user_data.get("quality", DEFAULT_QUALITY)
    style = context.user_data.get("style", DEFAULT_STYLE)
    preset = prompt_builder.get_preset(quality)
    generation_prompt = prompt_builder.build(prompt, quality, style)
    image_count = context.user_data.get("image_count", DEFAULT_IMAGE_COUNT)

    # Send "generating" message
    processing_msg = await update.message.reply_text(
        f"🎨 Generating image... quality={quality}, style={style}, count={image_count}"
    )
    
    generated_paths = []
    try:
        for i in range(image_count):
            output_path = _build_archive_output_path(user.id, prompt, i + 1)
            image_path = text_to_image(
                prompt=generation_prompt,
                output_path=output_path,
                aspect_ratio=preset.get("aspect_ratio"),
                image_size=preset.get("image_size"),
                model="google/gemini-3-flash-preview",
            )
            generated_paths.append(image_path)

            with open(image_path, "rb") as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=f"✅ Generated {i + 1}/{image_count} from: {prompt}"
                )

        publish_msg = None
        if ENABLE_DOUYIN_IMAGE_PUBLISH:
            publish_msg = await update.message.reply_text("📤 正在自动发布到抖音图文...")

        publish_result = await generate_and_publish_to_douyin(
            prompt=prompt,
            image_paths=generated_paths,
            publish_enabled=ENABLE_DOUYIN_IMAGE_PUBLISH,
            title=prompt,
            tags=DOUYIN_EXTRA_TAGS,
            account_file=DOUYIN_ACCOUNT_FILE or None,
            handle_login=DOUYIN_LOGIN_INTERACTIVE,
        )

        if publish_msg and publish_result.get("publish_status") == "success":
            await publish_msg.edit_text("✅ 抖音图文发布成功")
        elif publish_msg and publish_result.get("publish_status") == "failed":
            publish_error = publish_result.get("publish_error", "unknown error")
            logger.warning("Douyin publish failed: %s", publish_error)
            await publish_msg.edit_text(f"⚠️ 抖音发布失败: {publish_error}")

        await processing_msg.delete()
        
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        await processing_msg.edit_text(f"❌ Error generating image: {str(e)}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")


def main():
    """Main function to run the bot"""
    # Check if token is set
    if not TG_BOT_TOKEN:
        print("❌ TG_BOT_TOKEN is not set!")
        print("Please set the TG_BOT_TOKEN environment variable.")
        print("You can get a bot token from @BotFather on Telegram.")
        return
    
    print("🚀 Starting Telegram Bot...")
    print("📝 Bot will generate images using OpenRouter API")
    
    # Create application
    builder = Application.builder().token(TG_BOT_TOKEN)
    if PROXY_URL:
        builder = builder.proxy_url(PROXY_URL).get_updates_proxy_url(PROXY_URL)
    application = builder.build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("quality", quality_command))
    application.add_handler(CommandHandler("style", style_command))
    application.add_handler(CommandHandler("count", count_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start polling
    print("✅ Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
