import logging
import pytz
from datetime import datetime, time
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 1. إعدادات التوقيت الصارمة (مصر)
MY_TZ = pytz.timezone('Africa/Cairo')

# 2. قائمة الـ IDs المصححة
GROUP_IDS = [
    -1003870414631, -1003868568456, -1003843038200, -1003842260078,
    -1003773422592, -1003309198838, -1003544491812, -1003715228581,
    -1003304815564, -1003835237780, -1003851844806, -1003863374316
]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = "8685861366:AAFKP3Nm1RG8wVx4k0aQf1KKEneCXf22ja8"

# ---------------- وظائف الأمان والتحقق ----------------

async def is_admin(update: Update):
    """فحص هل المستخدم أدمن أو صاحب الجروب"""
    try:
        user_status = await update.effective_chat.get_member(update.effective_user.id)
        return user_status.status in ['administrator', 'creator']
    except:
        return False

# ---------------- وظيفة تنفيذ الأوامر ----------------

async def set_group_status(context, chat_id, is_open):
    if is_open:
        perms = ChatPermissions(
            can_send_messages=True, can_send_photos=True, can_send_videos=True,
            can_send_video_notes=True, can_send_documents=True,
            can_send_other_messages=False, can_add_web_page_previews=False,
            can_send_polls=False, can_send_voice_notes=False, can_send_audios=False
        )
    else:
        perms = ChatPermissions(can_send_messages=False)
    
    try:
        await context.bot.set_chat_permissions(chat_id=chat_id, permissions=perms)
    except Exception as e:
        logging.error(f"❌ خطأ في الجerوب {chat_id}: {e}")

# ---------------- المحرك المجدول ----------------

async def scheduled_task(context: ContextTypes.DEFAULT_TYPE):
    now_in_egypt = datetime.now(MY_TZ)
    if now_in_egypt.weekday() in [1, 4]: # الثلاثاء والجمعة إجازة
        return
    chat_id, action = context.job.data
    await set_group_status(context, chat_id, (action == "open"))

# ---------------- الأوامر اليدوية (للأدمن فقط) ----------------

async def open_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update): return
    await set_group_status(context, update.effective_chat.id, True)
    await update.message.reply_text("🔓 تم فتح الجروب (بأمر الأدمن).")

async def close_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update): return
    await set_group_status(context, update.effective_chat.id, False)
    await update.message.reply_text("🔒 تم قفل الجروب فوراً (بأمر الأدمن).")

async def addtime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إضافة ميعاد فتح وقفل في أمر واحد"""
    if not await is_admin(update): return
    
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ المثال: /addtime 14:00 14:15\n(الأول فتح والتاني قفل)")
        return
        
    try:
        # الميعاد الأول (الفتح)
        h1, m1 = map(int, context.args[0].split(':'))
        # الميعاد الثاني (القفل)
        h2, m2 = map(int, context.args[1].split(':'))
        
        t_open = time(hour=h1, minute=m1, tzinfo=MY_TZ)
        t_close = time(hour=h2, minute=m2, tzinfo=MY_TZ)
        
        # جدولة الفتح
        context.job_queue.run_daily(scheduled_task, time=t_open, data=(update.effective_chat.id, "open"))
        # جدولة القفل
        context.job_queue.run_daily(scheduled_task, time=t_close, data=(update.effective_chat.id, "close"))
        
        await update.message.reply_text(f"✅ تم الجدولة الإضافية:\n🔓 فتح: {context.args[0]}\n🔒 قفل: {context.args[1]}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ في الصيغة: {e}")

# ---------------- تشغيل وإدارة البوت ----------------

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    jq = app.job_queue

    # المواعيد الثابتة (السيستم العسكري الأصلي)
    for gid in GROUP_IDS:
        for t, act in [((8,0), "open"), ((8,15), "close"), ((8,45), "open"), ((9,0), "close"), ((21,0), "open"), ((22,0), "close")]:
            jq.run_daily(scheduled_task, time=time(hour=t[0], minute=t[1], tzinfo=MY_TZ), data=(gid, act))

    app.add_handler(CommandHandler("open_now", open_now))
    app.add_handler(CommandHandler("close_now", close_now))
    app.add_handler(CommandHandler("addtime", addtime))

    print("🚀 البوت انطلق.. نظام الـ (فتح وقفل) في سطر واحد جاهز.")
    app.run_polling()

if __name__ == "__main__":
    main()
