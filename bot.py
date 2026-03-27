import logging
import pytz
from datetime import datetime, time
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 1. إعدادات التوقيت الصارمة (مصر)
MY_TZ = pytz.timezone('Africa/Cairo')

# 2. قائمة الـ IDs المعتمدة (الـ 12 جروب)
GROUP_IDS = [
    -1003870414631, -1003868568456, -1003843038200, -1003842260078,
    -1003773422592, -1003309198838, -1003544491812, -1003715228581,
    -1003304815564, -1003835237780, -1003851844806, -1003863374316
]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = "8685861366:AAFKP3Nm1RG8wVx4k0aQf1KKEneCXf22ja8"

# ---------------- وظائف التحقق (للأدمن فقط) ----------------

async def is_admin(update: Update):
    try:
        user_status = await update.effective_chat.get_member(update.effective_user.id)
        return user_status.status in ['administrator', 'creator']
    except Exception:
        return False

# ---------------- وظيفة التحكم في الصلاحيات ----------------

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
        logging.error(f"❌ فشل تنفيذ الصلاحيات للجروب {chat_id}: {e}")

# ---------------- المحرك (1): للمواعيد الثابتة (يحترم الإجازة) ----------------

async def fixed_scheduled_task(context: ContextTypes.DEFAULT_TYPE):
    now_in_egypt = datetime.now(MY_TZ)
    # 1=الثلاثاء, 4=الجمعة
    if now_in_egypt.weekday() in [1, 4]:
        logging.info("⏸️ اليوم إجازة (ثلاثاء/جمعة). تخطي الميعاد الثابت.")
        return
    chat_id, action = context.job.data
    await set_group_status(context, chat_id, (action == "open"))

# ---------------- المحرك (2): للأوامر الإضافية (يعمل دوماً) ----------------

async def extra_scheduled_task(context: ContextTypes.DEFAULT_TYPE):
    chat_id, action = context.job.data
    await set_group_status(context, chat_id, (action == "open"))
    logging.info(f"✅ تم تنفيذ أمر استثنائي ({action}) بنجاح.")

# ---------------- الأوامر اليدوية (للأدمن فقط) ----------------

async def open_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update): return
    await set_group_status(context, update.effective_chat.id, True)
    await update.message.reply_text("🔓 تم فتح الجروب فوراً.")

async def close_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update): return
    await set_group_status(context, update.effective_chat.id, False)
    await update.message.reply_text("🔒 تم قفل الجروب فوراً.")

async def addtime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update): return
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ المثال: /addtime 14:00 14:15")
        return
    try:
        h1, m1 = map(int, context.args[0].split(':'))
        h2, m2 = map(int, context.args[1].split(':'))
        
        # تنفيذ "لمرة واحدة" اليوم لتجنب التعارض مع الإجازات
        context.job_queue.run_once(extra_scheduled_task, when=time(hour=h1, minute=m1, tzinfo=MY_TZ), data=(update.effective_chat.id, "open"))
        context.job_queue.run_once(extra_scheduled_task, when=time(hour=h2, minute=m2, tzinfo=MY_TZ), data=(update.effective_chat.id, "close"))
        
        await update.message.reply_text(f"✅ تم جدولة ميعاد استثنائي لليوم:\n🔓 فتح: {context.args[0]}\n🔒 قفل: {context.args[1]}\n(سيعمل حتى لو كان اليوم إجازة)")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: تأكد من كتابة الوقت بشكل صحيح 14:00")

# ---------------- تشغيل السيستم ----------------

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    jq = app.job_queue

    # برمجة الـ 12 جروب بالمواعيد الـ 6 الثابتة
    for gid in GROUP_IDS:
        for t, act in [((8,0), "open"), ((8,15), "close"), ((8,45), "open"), ((9,0), "close"), ((21,0), "open"), ((22,0), "close")]:
            jq.run_daily(fixed_scheduled_task, time=time(hour=t[0], minute=t[1], tzinfo=MY_TZ), data=(gid, act))

    app.add_handler(CommandHandler("open_now", open_now))
    app.add_handler(CommandHandler("close_now", close_now))
    app.add_handler(CommandHandler("addtime", addtime))

    print("🚀 النظام العسكري يعمل بكامل طاقته..")
    app.run_polling()

if __name__ == "__main__":
    main()
