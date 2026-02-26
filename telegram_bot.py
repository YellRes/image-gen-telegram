"""
Telegram Bot for Image Generation
Receives messages from Telegram and generates images using Minimax API
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Import our text to image module
from text_to_image import text_to_image

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
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_GROUP_ID = os.getenv("MINIMAX_GROUP_ID", "")

# Per-user quality presets (Minimax image_generation has no direct quality field).
QUALITY_PRESETS = {
    "low": {
        "label": "低质量(更快)",
        "aspect_ratio": "1:1",
        "prompt_suffix": "simple composition, fewer details",
    },
    "medium": {
        "label": "中质量(平衡)",
        "aspect_ratio": "1:1",
        "prompt_suffix": "clean composition, natural lighting",
    },
    "high": {
        "label": "高质量(更慢)",
        "aspect_ratio": "1:1",
        "prompt_suffix": "highly detailed, sharp focus, cinematic lighting",
    },
}
DEFAULT_QUALITY = "medium"
DEFAULT_IMAGE_COUNT = 1
MAX_IMAGE_COUNT = 4

# States for conversation
(
    WAITING_FOR_PROMPT,
    WAITING_FOR_SIZE,
) = range(2)


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
    
    if MINIMAX_API_KEY:
        status.append("✅ Minimax API Key: Configured")
    else:
        status.append("❌ Minimax API Key: NOT SET (MINIMAX_API_KEY)")
    
    if MINIMAX_GROUP_ID:
        status.append("ℹ️ Minimax Group ID: Configured (optional)")
    else:
        status.append("ℹ️ Minimax Group ID: NOT SET (optional)")

    quality = context.user_data.get("quality", DEFAULT_QUALITY)
    quality_label = QUALITY_PRESETS.get(quality, QUALITY_PRESETS[DEFAULT_QUALITY])["label"]
    status.append(f"🎛️ Current Quality: {quality} ({quality_label})")
    image_count = context.user_data.get("image_count", DEFAULT_IMAGE_COUNT)
    status.append(f"🖼️ Current Image Count: {image_count}")
    
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
    if not MINIMAX_API_KEY:
        await update.message.reply_text(
            "❌ Bot is not properly configured. Please set MINIMAX_API_KEY environment variable."
        )
        return
    
    quality = context.user_data.get("quality", DEFAULT_QUALITY)
    preset = QUALITY_PRESETS.get(quality, QUALITY_PRESETS[DEFAULT_QUALITY])
    image_count = context.user_data.get("image_count", DEFAULT_IMAGE_COUNT)
    generation_prompt = f"{prompt}, {preset['prompt_suffix']}"

    # Send "generating" message
    processing_msg = await update.message.reply_text(
        f"🎨 Generating image... quality={quality}, count={image_count}"
    )
    
    generated_paths = []
    try:
        for i in range(image_count):
            output_path = f"temp/{user.id}_{hash(prompt)}_{i + 1}.jpeg"
            image_path = text_to_image(
                prompt=generation_prompt,
                output_path=output_path,
                aspect_ratio=preset["aspect_ratio"],
                model="image-01",
            )
            generated_paths.append(image_path)

            with open(image_path, "rb") as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=f"✅ Generated {i + 1}/{image_count} from: {prompt}"
                )

        await processing_msg.delete()
        
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        await processing_msg.edit_text(f"❌ Error generating image: {str(e)}")
    finally:
        for path in generated_paths:
            try:
                os.remove(path)
            except Exception:
                pass


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
    print(f"📝 Bot will generate images using Minimax API")
    
    # Create application
    application = Application.builder().token(TG_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("quality", quality_command))
    application.add_handler(CommandHandler("count", count_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start polling
    print("✅ Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
