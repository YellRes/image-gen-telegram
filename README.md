# Telegram Image Gen

Text to Image using Minimax API with Telegram Bot integration

## Features

- 🎨 Text to Image generation using Minimax API
- 🤖 Telegram Bot interface - send text and get images
- ⚙️ Easy configuration via environment variables

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
# Copy .env.example to .env and fill in your credentials
cp .env.example .env
```

Or set environment variables:
```bash
export TG_BOT_TOKEN=your-telegram-bot-token
export MINIMAX_API_KEY=your-minimax-api-key
export MINIMAX_GROUP_ID=your-minimax-group-id
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
python text_to_image.py "A beautiful sunset" -o output.png --width 1024 --height 1024
```

### Python Code
```python
from text_to_image import text_to_image

result = text_to_image(
    prompt="Your text description",
    output_path="output.png",
    width=1024,
    height=1024
)
```

### Telegram Bot
Just send any text to your bot and it will generate an image!

## Get API Keys

### Telegram Bot Token
1. Open Telegram and search for @BotFather
2. Use /newbot command
3. Follow instructions to create bot
4. Copy the token

### Minimax API
1. Visit https://platform.minimax.chat/
2. Sign up / Sign in
3. Create API key in dashboard
4. Get Group ID from your account settings

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
