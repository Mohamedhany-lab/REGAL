import logging
import pytz
from datetime import time
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 1. إعدادات التوقيت (مصر)
MY_TZ = pytz.timezone('Africa/Cairo')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "8685861366:AAFKP3Nm1RG8wVx4k0aQf1KKEneCXf22ja8" # حط التوكن بتاعك هنا

# ---------------- وظيفة التحكم في الصلاحيات ----------------

async def set_group_status(context, chat_id, is_open):
    if is_open:
        # فتح الصلاحيات (ما عدا الريكوردات والملفات الصوتية)
        perms = ChatPermissions(
            can_send_messages=True,         # الرسايل النصية
            can_send_photos=True,           # الصور
            can_send_videos=True,           # الفيديوهات
            can_send_documents=True,        # الملفات (PDF, الخ)
            can_send_other_messages=True,   # الاستيكرز والـ GIF
            can_add_web_page_previews=True, # لينكات المواقع
            can_send_polls=True,            # التصويتات
            # تم تعطيل الريكوردات والأغاني بناءً على طلبك:
            can_send_voice_notes=False,     # الريكوردات (ممنوع)
            can_send_audios=False           # الملفات الصوتية/الأغاني (ممنوع)
        )
    else:
        # قفل إرسال كل شيء
        perms = ChatPermissions(can_send_messages=False)
    
    return await context.bot.set_chat_permissions(chat_id=chat_id, permissions=perms)

# ---------------- الوظيفة المجدولة ----------------

async def scheduled_task(context: ContextTypes.DEFAULT_TYPE):
    chat_id, action = context.job.data
    is_open = (action == "open")
    await set_group_status(context, chat_id, is_open)
    logging.info(f"تم تنفيذ العملية: {action} للجروب {chat_id}")

# ---------------- أوامر الاختبار الفوري ----------------

async def close_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await set_group_status(context, update.effective_chat.id, False)
        await update.message.reply_text("🔒 تم قفل الجروب فوراً.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

async def open_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await set_group_status(context, update.effective_chat.id, True)
        await update.message.reply_text("🔓 تم فتح الجروب (الريكوردات ممنوعة).")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

# ---------------- أمر جدولة الوقت ----------------

async def addtime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.job_queue:
        await update.message.reply_text("❌ خطأ: الجدولة غير مفعلة. تأكد من [job-queue] في الـ requirements.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("⚠️ المثال: /addtime 22:00 close")
        return

    try:
        time_input = context.args[0]
        action = context.args[1].lower()
        
        h, m = map(int, time_input.split(':'))
        target_time = time(hour=h, minute=m, tzinfo=MY_TZ)

        job_name = f"{update.effective_chat.id}_{action}"

        # مسح القديم
        for job in context.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()

        # الجدولة اليومية
        context.job_queue.run_daily(
            scheduled_task,
            time=target_time,
            data=(update.effective_chat.id, action),
            name=job_name
        )
        await update.message.reply_text(f"✅ تم الجدولة: {action} الساعة {time_input} بتوقيت مصر.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

# ---------------- تشغيل البوت ----------------

def main():
    # بناء البوت مع تفعيل JobQueue تلقائياً
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("addtime", addtime))
    app.add_handler(CommandHandler("open_now", open_now))
    app.add_handler(CommandHandler("close_now", close_now))

    print("البوت يعمل والجدولة مفعلة (توقيت القاهرة)...")
    app.run_polling()

if __name__ == "__main__":
    main()
