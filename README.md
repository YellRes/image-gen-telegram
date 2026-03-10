# Telegram Image Gen

Text to Image using OpenRouter API with Telegram Bot integration

## Features

- 🎨 Text to Image generation using OpenRouter API
- 🤖 Telegram Bot interface - send text and get images
- 💾 Auto archive generated images to `images/YYYY/MM/DD/`
- ⚙️ Easy configuration via environment variables

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

2. Configure environment variables:
```bash
# Copy .env.example to .env and fill in your credentials
cp .env.example .env
```

Or set environment variables:
```bash
export TG_BOT_TOKEN=your-telegram-bot-token
export OPEN_ROUTER_KEY=your-openrouter-api-key
```

Windows PowerShell example:
```powershell
$env:TG_BOT_TOKEN="your-telegram-bot-token"
$env:OPEN_ROUTER_KEY="your-openrouter-api-key"
```

## Telegram Bot Setup

### 1. Create a Bot

1. Open Telegram and search for @BotFather
2. Send `/newbot` to create a new bot
3. Follow the instructions and get your bot token
4. Copy the token to TG_BOT_TOKEN in your .env file

### 2. Start the Bot

```bash
python telegram_bot.py
```

### 3. Use the Bot

1. Open your bot in Telegram
2. Send `/start` to get started
3. Send any text description
4. The bot will generate an image and send it back to you

## Commands

- `/start` - Welcome message and help
- `/help` - Usage instructions
- `/status` - Check configuration status

## Usage

### Command Line (without Telegram)
```bash
python text_to_image.py "A beautiful sunset" -o output.png --model google/gemini-3-flash-preview
```

### Python Code
```python
from text_to_image import text_to_image

result = text_to_image(
    prompt="Your text description",
    output_path="output.png",
    model="google/gemini-3-flash-preview"
)
```

### Telegram Bot
Just send any text to your bot and it will generate an image.

Generated images are archived locally by date:
- `images/YYYY/MM/DD/`
- Files are kept by default and will not be deleted after sending.

## Douyin Auto Publish (Image Post)

When enabled, the bot will publish generated images to Douyin creator center automatically.

1. Prepare Playwright and dependencies:
```powershell
pip install -r requirements.txt
playwright install chromium
```

2. Configure `.env`:
```dotenv
ENABLE_DOUYIN_IMAGE_PUBLISH=true
DOUYIN_ACCOUNT_FILE=
DOUYIN_LOGIN_INTERACTIVE=false
DOUYIN_PUBLISH_TAGS=AI绘画,自动发布
```

3. Generate/refresh Douyin cookie once (interactive login):
```powershell
python verify_douyin_image_publish.py --title "登录初始化" --images .\temp\sample.jpeg --interactive-login
```

4. Start Telegram bot:
```powershell
python telegram_bot.py
```

5. Minimal publish verification (without Telegram):
```powershell
python verify_douyin_image_publish.py --title "自动发布测试" --images .\temp\1.jpeg .\temp\2.jpeg --tags AI 自动化
```

## Get API Keys

### Telegram Bot Token
1. Open Telegram and search for @BotFather
2. Use /newbot command
3. Follow instructions to create bot
4. Copy the token

### OpenRouter API
1. Visit https://openrouter.ai/
2. Sign up / Sign in
3. Create API key in dashboard
4. Put it into `OPEN_ROUTER_KEY`

## Project Structure

```
telegram-image-gen/
├── text_to_image.py      # Core text-to-image module
├── telegram_bot.py       # Telegram Bot implementation
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
├── README.md             # This file
└── example.py           # Usage examples
```
