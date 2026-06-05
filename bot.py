import os
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# تنظیمات
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
YOUR_NAME = os.environ.get("YOUR_NAME", "دستیار")

# تنظیم Groq
client = Groq(api_key=GROQ_API_KEY)

# حافظه مکالمه برای هر کاربر
conversations = {}

# شخصیت ربات - قوی و دقیق مثل Claude
SYSTEM_PROMPT = f"""تو یک دستیار هوش مصنوعی بسیار پیشرفته و باهوش هستی که به جای {YOUR_NAME} جواب میدی.

شخصیت و سبک جواب دادن تو:
- کامل، دقیق و جامع جواب بده — هیچ چیز مهمی رو حذف نکن
- وقتی سوال فنی یا آموزشی میاد، قدم به قدم و با جزئیات کامل توضیح بده
- وقتی سوال ساده‌ست، کوتاه و مستقیم جواب بده
- همیشه صادق باش — اگه چیزی نمیدونی بگو نمیدونم
- گرم، صمیمی و مودب باش ولی بیش از حد تعریف نکن
- هیچوقت سوال رو تکرار نکن، مستقیم برو سر اصل مطلب
- از ایموجی فقط وقتی طبیعیه استفاده کن، نه در هر جمله
- به فارسی روان و طبیعی صحبت کن، نه رسمی و خشک
- اگه کسی کمک فنی، کد، راهنمایی یا توضیح میخواد، کامل‌ترین جواب ممکن رو بده
- تاریخچه مکالمه رو در نظر بگیر و منسجم باش
- هیچوقت نگو "به عنوان یک هوش مصنوعی..." — فقط جواب بده
- اگه به زبان دیگه‌ای نوشتن، همون زبان جواب بده"""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_message = update.message.text

    if user_id not in conversations:
        conversations[user_id] = []

    conversations[user_id].append({
        "role": "user",
        "content": user_message
    })

    if len(conversations[user_id]) > 30:
        conversations[user_id] = conversations[user_id][-30:]

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT}
            ] + conversations[user_id],
            max_tokens=1500,
            temperature=0.7
        )

        reply = response.choices[0].message.content

        conversations[user_id].append({
            "role": "assistant",
            "content": reply
        })

    except Exception as e:
        reply = "یه مشکلی پیش اومد، دوباره امتحان کن 🙏"
        print(f"Error: {e}")

    await update.message.reply_text(reply)

def main():
    print(f"ربات {YOUR_NAME} شروع به کار کرد! ✅")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
