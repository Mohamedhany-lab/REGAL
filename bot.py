import logging
import pytz
from datetime import datetime, time, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 1. التوقيت المصري الصارم (القاهرة)
MY_TZ = pytz.timezone('Africa/Cairo')

# 2. قائمة الـ 13 جروب المعتمدة
GROUP_IDS = [
    -1003870414631, -1003868568456, -1003843038200, -1003842260078,
    -1003773422592, -1003309198838, -1003544491812, -1003715228581,
    -1003304815564, -1003835237780, -1003851844806, -1003863374316,
    -1003843038200
]

TOKEN = "8685861366:AAFKP3Nm1RG8wVx4k0aQf1KKEneCXf22ja8"

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# ---------------- وظيفة التنفيذ القهرية (تطبيق الصلاحيات) ----------------

async def apply_status(bot, chat_id, action):
    """فتح أو قفل الجروب بناءً على الطلب مع صلاحيات محددة"""
    is_open = (action == "open")
    if is_open:
        perms = ChatPermissions(
            can_send_messages=True, can_send_photos=True, can_send_videos=True,
            can_send_video_notes=True, can_send_documents=True,
            can_send_other_messages=False, can_add_web_page_previews=False,
            can_send_polls=False, can_send_voice_notes=False, can_send_audios=False
        )
        # السطر المضاف فقط:
        alert_msg = "تنبيه عسكري 🪖:\n\"الجروبات مفتوحة الان\""
    else:
        perms = ChatPermissions(can_send_messages=False)
        # السطر المضاف فقط:
        alert_msg = "تنبيه عسكري 🪖:\n\"مقفولة تماماً الآن\""
    
    try:
        await bot.set_chat_permissions(chat_id=int(chat_id), permissions=perms)
        # السطر المضاف فقط لإرسال الرسالة:
        await bot.send_message(chat_id=int(chat_id), text=alert_msg)
        logging.info(f"✅ ACTION SUCCESS: {action} on {chat_id}")
        return True
    except Exception as e:
        logging.error(f"❌ ACTION FAILED: {chat_id} | {e}")
        return False

# ---------------- المحرك الذكي للمواعيد (Job Trigger) ----------------

async def job_trigger(context: ContextTypes.DEFAULT_TYPE):
    chat_id, action, is_fixed = context.job.data
    if is_fixed:
        now_egypt = datetime.now(MY_TZ)
        if now_egypt.weekday() in [1, 4]: 
            logging.info(f"⏸️ Holiday Skip (Fixed Schedule): {chat_id}")
            return
    await apply_status(context.bot, chat_id, action)

# ---------------- أوامر التحكم (أدمن فقط) ----------------

async def is_admin(update: Update):
    try:
        user = await update.effective_chat.get_member(update.effective_user.id)
        return user.status in ['administrator', 'creator']
    except: return False

async def addtime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update): return
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ المثال: /addtime 05:30 06:00")
        return
    try:
        now_eg = datetime.now(MY_TZ)
        h1, m1 = map(int, context.args[0].split(':'))
        h2, m2 = map(int, context.args[1].split(':'))
        t_open_dt = now_eg.replace(hour=h1, minute=m1, second=0, microsecond=0)
        t_close_dt = now_eg.replace(hour=h2, minute=m2, second=0, microsecond=0)
        if t_open_dt <= now_eg:
            await apply_status(context.bot, update.effective_chat.id, "open")
            msg = "🔓 الميعاد حان فعلاً: تم كسر القفل والفتح فوراً."
        else:
            context.job_queue.run_once(job_trigger, when=t_open_dt, data=(update.effective_chat.id, "open", False))
            msg = f"✅ ميعاد الفتح القادم: {context.args[0]}"
        context.job_queue.run_once(job_trigger, when=t_close_dt, data=(update.effective_chat.id, "close", False))
        await update.message.reply_text(f"{msg}\n🔒 ميعاد القفل المجدول: {context.args[1]}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ فني: {e}")

async def open_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update): return
    await apply_status(context.bot, update.effective_chat.id, "open")

async def close_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update): return
    await apply_status(context.bot, update.effective_chat.id, "close")

# ---------------- تشغيل السيستم المركزي ----------------

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    jq = app.job_queue
    for gid in GROUP_IDS:
        daily_schedule = [
            ((8,0), "open"), ((8,15), "close"), 
            ((8,45), "open"), ((9,0), "close"), 
            ((21,0), "open"), ((22,0), "close")
        ]
        for t, act in daily_schedule:
            jq.run_daily(job_trigger, time=time(t[0], t[1], tzinfo=MY_TZ), data=(gid, act, True))
    app.add_handler(CommandHandler("open_now", open_now))
    app.add_handler(CommandHandler("close_now", close_now))
    app.add_handler(CommandHandler("addtime", addtime))
    print("🚀 نظام التحكم الشامل يعمل الآن (13 ID).. المواعيد ثابتة والتحصينات مفعلة.")
    app.run_polling()

if __name__ == "__main__":
    main()
