import logging
import pytz
from datetime import time
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 1. إعداد التوقيت (مهم جداً عشان Railway شغال توقيت جرينتش)
# لو انت في مصر سيبها 'Africa/Cairo' لو في السعودية خليها 'Asia/Riyadh'
MY_TZ = pytz.timezone('Africa/Cairo') 

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

TOKEN = "8685861366:AAFKP3Nm1RG8wVx4k0aQf1KKEneCXf22ja8"

# ---------------- وظيفة تغيير الصلاحيات (الأساسية) ----------------

async def set_group_status(context, chat_id, is_open):
    """وظيفة موحدة لتغيير صلاحيات الجروب"""
    perms = ChatPermissions(
        can_send_messages=is_open,
        can_send_media_messages=is_open,
        can_send_polls=is_open,
        can_add_web_page_previews=is_open
    )
    return await context.bot.set_chat_permissions(chat_id=chat_id, permissions=perms)

# ---------------- الوظائف التي يتم استدعاؤها في الموعد ----------------

async def scheduled_task(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id, action = job.data
    is_open = (action == "open")
    
    try:
        await set_group_status(context, chat_id, is_open)
        logging.info(f"تم تنفيذ الموعد بنجاح: {action} للجروب {chat_id}")
    except Exception as e:
        logging.error(f"فشل تنفيذ الموعد: {e}")

# ---------------- أوامر الاختبار الفوري ----------------

async def open_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        await set_group_status(context, chat_id, True)
        await update.message.reply_text("🔓 تم فتح الجروب فوراً للاختبار.")
    except Exception as e:
        await update.message.reply_text(f"❌ فشل الفتح: {e}\n(تأكد أن البوت أدمن)")

async def close_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        await set_group_status(context, chat_id, False)
        await update.message.reply_text("🔒 تم قفل الجروب فوراً للاختبار.")
    except Exception as e:
        await update.message.reply_text(f"❌ فشل القفل: {e}\n(تأكد أن البوت أدمن)")

# ---------------- أمر ضبط المواعيد اليومية ----------------

async def addtime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # التأكد من المدخلات
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ طريقة الاستخدام:\n/addtime 22:00 close\nأو\n/addtime 08:00 open")
        return

    try:
        time_input = context.args[0]
        action = context.args[1].lower()
        
        if action not in ['open', 'close']:
            await update.message.reply_text("❌ الأكشن لازم يكون open أو close")
            return

        h, m = map(int, time_input.split(':'))
        # تحديد الوقت بناءً على المنطقة الزمنية
        target_time = time(hour=h, minute=m, tzinfo=MY_TZ)

        # اسم فريد لكل نوع (قفل أو فتح) عشان ميمسحوش بعض
        job_name = f"{chat_id}_{action}"

        # مسح أي موعد قديم متسجل لنفس النوع في الجروب ده
        current_jobs = context.job_queue.get_jobs_by_name(job_name)
        for job in current_jobs:
            job.schedule_removal()

        # جدولة المهمة يومياً
        context.job_queue.run_daily(
            scheduled_task,
            time=target_time,
            data=(chat_id, action),
            name=job_name
        )

        await update.message.reply_text(f"✅ تم الضبط! الجروب سيقوم بـ ({action}) يومياً الساعة {time_input} بتوقيتك المحلي.")

    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ في التنسيق. تأكد من كتابة الوقت HH:MM\n(مثال: 09:30)")

# ---------------- تشغيل البوت ----------------

def main():
    # هنا شيلنا الـ Persistence مؤقتاً لسهولة التجربة
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("addtime", addtime))
    app.add_handler(CommandHandler("open_now", open_now))
    app.add_handler(CommandHandler("close_now", close_now))

    print("البوت شغال الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
