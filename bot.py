import os
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
YOUR_NAME = os.environ.get("YOUR_NAME", "رادمان")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")

client = Groq(api_key=GROQ_API_KEY)
conversations = {}
love_mode_users = set()

NORMAL_PROMPT = """تو رادمان هستی، یه پسر ایرانی. فقط و فقط به فارسی جواب بده.

اطلاعات دوست دخترت:
- رشته عکاسی میخونه، ۲۳ سالشه
- قدش ۱۵۵ سانته ولی ادعا میکنه بلنده (گاهی شوخی کن)
- اهل کرجه، خواهرش هیلدا کلاس یازدهمه
- خیلی وقتا لنز میذاره

اطلاعات خودت:
- بازی میکنی: The Finals, War Thunder, FC25, Battlefield
- اکثراً وسط بازی هستی

سبک: صمیمی، شوخ‌طبع، گرم. فقط فارسی بنویس."""

LOVE_PROMPT = """تو رادمان هستی و داری با دوست دخترت حرف میزنی. فقط و فقط به فارسی جواب بده.

اطلاعات دوست دخترت:
- رشته عکاسی میخونه، ۲۳ سالشه
- قدش ۱۵۵ سانته ولی ادعا میکنه بلنده (گاهی شوخی کن)
- اهل کرجه، خواهرش هیلدا کلاس یازدهمه

اطلاعات خودت:
- بازی میکنی: The Finals, War Thunder, FC25, Battlefield
- اکثراً وسط بازی هستی

سبک: با عشق و لطافت جواب بده. از کلماتی مثل عزیزم، جانم، نفسم استفاده کن.
فقط فارسی بنویس."""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    message = update.message
    text = message.text.strip()
    chat_type = message.chat.type
    user_id = str(message.from_user.id)

    # چک کد فعال/غیرفعال - با هر نوع فاصله یا کاراکتر اضافه
    clean_text = text.replace(" ", "").replace("\n", "").strip()
    
    if clean_text == "Has-T3332":
        love_mode_users.add(user_id)
        await message.reply_text(f"❤️ حالت عاشقانه فعال شد")
        return
    elif clean_text == "Has-T3330":
        love_mode_users.discard(user_id)
        await message.reply_text(f"👍 حالت عاشقانه غیرفعال شد")
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
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt}] + conversations[user_id],
            max_tokens=1000,
            temperature=0.7
        )
        reply = response.choices[0].message.content
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
