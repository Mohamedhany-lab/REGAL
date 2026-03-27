import logging
import pytz
from datetime import datetime, time
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 1. إعدادات التوقيت الصارمة (مصر)
MY_TZ = pytz.timezone('Africa/Cairo')

# 2. قائمة الـ IDs المصححة (إضافة -100 لكل رقم بعته)
GROUP_IDS = [
    -1003870414631, -1003868568456, -1003843038200, -1003842260078,
    -1003773422592, -1003309198838, -1003544491812, -1003715228581,
    -1003304815564, -1003835237780, -1003851844806, -1003863374316
]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "8685861366:AAFKP3Nm1RG8wVx4k0aQf1KKEneCXf22ja8"

# ---------------- وظيفة تنفيذ الأوامر ----------------

async def set_group_status(context, chat_id, is_open):
    if is_open:
        perms = ChatPermissions(
            can_send_messages=True,         # نص
            can_send_photos=True,           # صور
            can_send_videos=True,           # فيديو
            can_send_video_notes=True,      # نوت فيديو (كاميرا فورية)
            can_send_documents=True,        # ملفات
            can_send_other_messages=False,  # استيكرز و GIF (ممنوع)
            can_add_web_page_previews=False,# لينكات (ممنوع)
            can_send_polls=False,           # تصويت (ممنوع)
            can_send_voice_notes=False,     # ريكوردات (ممنوع)
            can_send_audios=False           # ملفات صوتية (ممنوع)
        )
    else:
        perms = ChatPermissions(can_send_messages=False)
    
    try:
        await context.bot.set_chat_permissions(chat_id=chat_id, permissions=perms)
    except Exception as e:
        logging.error(f"❌ فشل في تنفيذ الصلاحيات للجروب {chat_id}: {e}")

# ---------------- المحرك الذكي للجدولة ----------------

async def scheduled_task(context: ContextTypes.DEFAULT_TYPE):
    # فحص اليوم الحالي في مصر
    now_in_egypt = datetime.now(MY_TZ)
    current_day = now_in_egypt.weekday() # 1=Tuesday, 4=Friday
    
    if current_day in [1, 4]:
        logging.info("⏸️ اليوم إجازة رسمية (الثلاثاء أو الجمعة). البوت في وضع السكون.")
        return

    chat_id, action = context.job.data
    await set_group_status(context, chat_id, (action == "open"))
    logging.info(f"✅ تم تنفيذ {action} للجروب {chat_id} بنجاح.")

# ---------------- الأوامر اليدوية (للطوارئ) ----------------

async def open_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_group_status(context, update.effective_chat.id, True)
    await update.message.reply_text("🔓 تم فتح الجروب (النظام العسكري مفعل).")

async def close_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_group_status(context, update.effective_chat.id, False)
    await update.message.reply_text("🔒 تم قفل الجروب فوراً.")

# ---------------- تشغيل وإدارة البوت ----------------

def main():
    # بناء البوت مع دعم الـ JobQueue
    app = ApplicationBuilder().token(TOKEN).build()
    jq = app.job_queue

    # برمجة "المسامير" (الجدولة اليومية لكل الجروبات)
    for gid in GROUP_IDS:
        # الفترة 1: 08:00 ص - 08:15 ص
        jq.run_daily(scheduled_task, time=time(8, 0, tzinfo=MY_TZ), data=(gid, "open"))
        jq.run_daily(scheduled_task, time=time(8, 15, tzinfo=MY_TZ), data=(gid, "close"))
        
        # الفترة 2: 08:45 ص - 09:00 ص
        jq.run_daily(scheduled_task, time=time(8, 45, tzinfo=MY_TZ), data=(gid, "open"))
        jq.run_daily(scheduled_task, time=time(9, 0, tzinfo=MY_TZ), data=(gid, "close"))
        
        # الفترة 3: 09:00 م - 10:00 م (21:00 - 22:00)
        jq.run_daily(scheduled_task, time=time(21, 0, tzinfo=MY_TZ), data=(gid, "open"))
        jq.run_daily(scheduled_task, time=time(22, 0, tzinfo=MY_TZ), data=(gid, "close"))

    # تسجيل الأوامر
    app.add_handler(CommandHandler("open_now", open_now))
    app.add_handler(CommandHandler("close_now", close_now))

    print("🚀 البوت انطلق.. نظام الـ 12 جروب تحت السيطرة.")
    app.run_polling()

if __name__ == "__main__":
    main()
