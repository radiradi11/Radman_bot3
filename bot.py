import os
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# تنظیمات
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
YOUR_NAME = os.environ.get("YOUR_NAME", "من")

# تنظیم Groq
client = Groq(api_key=GROQ_API_KEY)

# حافظه مکالمه برای هر کاربر
conversations = {}

# شخصیت ربات
SYSTEM_PROMPT = f"""تو داری به جای {YOUR_NAME} جواب میدی.
- مودب، صمیمی و طبیعی صحبت کن
- پیام‌ها رو کوتاه نگه دار مثل پیام تلگرامی واقعی
- اگه سوال خیلی مهمی بود که مطمئن نیستی، بگو بعداً جواب میدم
- به فارسی جواب بده مگه اینکه طرف به زبان دیگه‌ای بنویسه
- سعی کن مثل {YOUR_NAME} فکر کنی و جواب بدی"""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_message = update.message.text

    # شروع مکالمه جدید برای کاربر جدید
    if user_id not in conversations:
        conversations[user_id] = []

    # اضافه کردن پیام کاربر
    conversations[user_id].append({
        "role": "user",
        "content": user_message
    })

    # فقط ۲۰ پیام آخر رو نگه دار
    if len(conversations[user_id]) > 20:
        conversations[user_id] = conversations[user_id][-20:]

    # نشون دادن حالت تایپ
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # رایگان و قوی
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT}
            ] + conversations[user_id],
            max_tokens=500
        )

        reply = response.choices[0].message.content

        # اضافه کردن جواب به تاریخچه
        conversations[user_id].append({
            "role": "assistant",
            "content": reply
        })

    except Exception as e:
        reply = "یه مشکلی پیش اومد، دوباره امتحان کن 🙏"
        print(f"Error: {e}")

    await update.message.reply_text(reply)

def main():
    print(f"ربات {YOUR_NAME} با Groq شروع به کار کرد! ✅")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
