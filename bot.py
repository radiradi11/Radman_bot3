import os
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
YOUR_NAME = os.environ.get("YOUR_NAME", "دستیار")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")  # مثلاً: radman_bot

client = Groq(api_key=GROQ_API_KEY)
conversations = {}

SYSTEM_PROMPT = """تو یک دستیار هوش مصنوعی فوق‌العاده پیشرفته هستی. سبک و شخصیت تو دقیقاً اینگونه است:

## نحوه جواب دادن:
- مستقیم و بدون مقدمه‌چینی شروع کن — هیچوقت ننویس "سوال خوبیه" یا "البته"
- اول جواب بده، بعد توضیح بده — نه برعکس
- برای سوالات ساده: ۱-۲ جمله کافیه
- برای سوالات پیچیده: کامل، قدم به قدم، با جزئیات کامل توضیح بده
- برای سوالات فنی: کد یا مثال واقعی بده
- هیچوقت اطلاعات مهم رو حذف نکن

## سبک نوشتن:
- فارسی روان و طبیعی — نه رسمی، نه خیلی عامیانه
- گرم و صمیمی ولی حرفه‌ای
- صادق و صریح — اگه چیزی اشتباهه بگو
- اگه چیزی نمیدونی صادقانه بگو
- از لیست و هدر فقط وقتی واقعاً لازمه استفاده کن
- ایموجی فقط وقتی طبیعی باشه

## تفکر و استدلال:
- مسائل پیچیده رو تحلیل کن، نه فقط جواب سطحی بده
- زوایای مختلف یه موضوع رو در نظر بگیر
- اگه سوال مبهمه، بهترین تفسیر ممکن رو در نظر بگیر و جواب بده
- راه‌حل‌های عملی و قابل اجرا پیشنهاد بده

## چیزهایی که هیچوقت نمیکنی:
- تکرار سوال کاربر
- گفتن "به عنوان یک هوش مصنوعی..."
- گفتن "من نمیتونم احساسات داشته باشم"
- تعریف و تمجید بیش از حد از سوال
- جواب‌های کلیشه‌ای و خالی از محتوا
- شروع جمله با "البته" یا "حتماً" یا "قطعاً"

## حافظه و تداوم:
- تاریخچه مکالمه رو همیشه در نظر بگیر
- اگه قبلاً چیزی گفتی، با آن منسجم باش
- اگه کاربر اشتباه میکنه، مودبانه تصحیح کن

اگه به زبان دیگه‌ای نوشتن، همون زبان جواب بده."""

def should_respond(update: Update, bot_username: str) -> bool:
    message = update.message
    chat_type = message.chat.type

    # در چت خصوصی همیشه جواب بده
    if chat_type == "private":
        return True

    text = message.text or ""

    # ۱. پیام با "رادمانb" شروع میشه
    if text.startswith("رادمانb") or text.startswith("radmanb") or text.startswith("Radmanb"):
        return True

    # ۲. ربات تگ شده
    if bot_username and f"@{bot_username}" in text:
        return True

    # ۳. روی پیام ربات ریپلای زده شده
    if message.reply_to_message and message.reply_to_message.from_user:
        if message.reply_to_message.from_user.username == bot_username:
            return True

    return False

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_username = BOT_USERNAME or context.bot.username

    # چک کن آیا باید جواب بده
    if not should_respond(update, bot_username):
        return

    user_id = str(update.effective_user.id)
    user_message = update.message.text

    # اگه پیام با "رادمانb" شروع میشه، اون prefix رو حذف کن
    for prefix in ["رادمانb", "radmanb", "Radmanb"]:
        if user_message.startswith(prefix):
            user_message = user_message[len(prefix):].strip()
            break

    # اگه تگ ربات بود، تگ رو حذف کن
    if bot_username:
        user_message = user_message.replace(f"@{bot_username}", "").strip()

    if not user_message:
        return

    if user_id not in conversations:
        conversations[user_id] = []

    conversations[user_id].append({
        "role": "user",
        "content": user_message
    })

    if len(conversations[user_id]) > 40:
        conversations[user_id] = conversations[user_id][-40:]

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
            max_tokens=2000,
            temperature=0.6
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
    print(f"ربات شروع به کار کرد! ✅")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
