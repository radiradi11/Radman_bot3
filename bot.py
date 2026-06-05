import os
import re
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")

client = Groq(api_key=GROQ_API_KEY)
conversations = {}
love_mode_users = set()

def has_non_persian_script(text):
    patterns = [
        r'[\u4e00-\u9fff]',  # چینی
        r'[\u3040-\u309f]',  # ژاپنی هیراگانا
        r'[\u30a0-\u30ff]',  # ژاپنی کاتاکانا
        r'[\u0400-\u04ff]',  # روسی
        r'[\uac00-\ud7af]',  # کره‌ای
    ]
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    return False

NORMAL_PROMPT = """You are a smart, warm, and helpful AI assistant. Always respond ONLY in Persian (Farsi).
Never use Chinese, Japanese, Russian, Korean or any non-Persian/Latin script.

Your personality:
- Friendly, natural, and conversational — not cold or robotic
- Responses are medium length — not too short, not too long
- You show genuine interest and care in what people say
- You're thoughtful and give real, useful answers
- Sometimes you ask a follow-up question to keep the conversation going
- You use casual Persian naturally — the way friends talk
- Never start with "البته" or "حتماً" or repeat the question
- Never say "as an AI..." — just talk naturally

Language rule: ONLY Persian script. No exceptions."""

LOVE_PROMPT = """You are a warm, loving, and caring AI assistant. Always respond ONLY in Persian (Farsi).
Never use Chinese, Japanese, Russian, Korean or any non-Persian/Latin script.

Your personality:
- Deeply warm, caring and loving in tone
- Use terms like عزیزم، جانم، نفسم naturally when it fits
- Responses are medium length — heartfelt but not overwhelming
- Supportive and emotionally present
- Help with whatever is asked with love and care
- Natural Persian — the way a loving person talks

Language rule: ONLY Persian script. No exceptions."""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    message = update.message
    text = message.text.strip()
    chat_type = message.chat.type
    user_id = str(message.from_user.id)

    clean_text = text.replace(" ", "").strip()

    if clean_text == "Has-T3332":
        love_mode_users.add(user_id)
        await message.reply_text("❤️ فعال شد")
        return
    elif clean_text == "Has-T3330":
        love_mode_users.discard(user_id)
        await message.reply_text("👍 غیرفعال شد")
        return

    if chat_type == "private":
        should_reply = True
    else:
        should_reply = False
        bot_username = BOT_USERNAME or context.bot.username or ""

        if bot_username and f"@{bot_username}" in text:
            should_reply = True
            text = text.replace(f"@{bot_username}", "").strip()

        triggers = ["رادمان", "radman", "Radman"]
        for trigger in triggers:
            if text.lower().startswith(trigger.lower()):
                should_reply = True
                text = text[len(trigger):].strip()
                break

        if message.reply_to_message and message.reply_to_message.from_user:
            reply_username = message.reply_to_message.from_user.username or ""
            if reply_username.lower() == bot_username.lower():
                should_reply = True

    if not should_reply or not text:
        return

    system_prompt = LOVE_PROMPT if user_id in love_mode_users else NORMAL_PROMPT

    if user_id not in conversations:
        conversations[user_id] = []

    conversations[user_id].append({"role": "user", "content": text})

    if len(conversations[user_id]) > 40:
        conversations[user_id] = conversations[user_id][-40:]

    await context.bot.send_chat_action(chat_id=message.chat_id, action="typing")

    try:
        reply = ""
        for attempt in range(3):
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_prompt}] + conversations[user_id],
                max_tokens=600,
                temperature=0.75
            )
            reply = response.choices[0].message.content

            if not has_non_persian_script(reply):
                break

        conversations[user_id].append({"role": "assistant", "content": reply})

    except Exception as e:
        reply = "یه مشکلی پیش اومد 🙏"
        print(f"Error: {e}")

    await message.reply_text(reply)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! آماده‌ام ✅")

def main():
    print("ربات شروع به کار کرد! ✅")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
