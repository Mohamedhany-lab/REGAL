import logging
import pytz
from datetime import datetime, time, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 1. التوقيت المصري الصارم
MY_TZ = pytz.timezone('Africa/Cairo')

# 2. قائمة الـ 13 جروب (تم إضافة الـ ID الجديد وتثبيته)
GROUP_IDS = [
    -1003870414631, -1003868568456, -1003843038200, -1003842260078,
    -1003773422592, -1003309198838, -1003544491812, -1003715228581,
    -1003304815564, -1003835237780, -1003851844806, -1003863374316,
    -1003843038200 # الـ ID الجديد المضاف
]

TOKEN = "8685861366:AAFKP3Nm1RG8wVx4k0aQf1KKEneCXf22ja8"

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# ---------------- وظيفة التنفيذ ----------------

async def apply_status(bot, chat_id, action):
    is_open = (action == "open")
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
        await bot.set_chat_permissions(chat_id=int(chat_id), permissions=perms)
        logging.info(f"✅ TEST EXECUTION: {action} on {chat_id}")
        return True
    except Exception as e:
        logging.error(f"❌ TEST FAILED: {chat_id} | {e}")
        return False

# ---------------- المحرك الذكي ----------------

async def job_trigger(context: ContextTypes.DEFAULT_TYPE):
    chat_id, action, is_fixed = context.job.data
    
    # [ملاحظة للاختبار]: تم إيقاف فلتر الجمعة مؤقتاً لتجربة المواعيد الثابتة الآن
    # if is_fixed:
    #     now_egypt = datetime.now(MY_TZ)
    #     if now_egypt.weekday() in [1, 4]: 
    #         return
            
    await apply_status(context.bot, chat_id, action)

# ---------------- الأوامر ----------------

async def is_admin(update: Update):
    try:
        user = await update.effective_chat.get_member(update.effective_user.id)
        return user.status in ['administrator', 'creator']
    except: return False

async def addtime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update): return
    try:
        now_eg = datetime.now(MY_TZ)
        h1, m1 = map(int, context.args[0].split(':'))
        h2, m2 = map(int, context.args[1].split(':'))
        t_open_dt = now_eg.replace(hour=h1, minute=m1, second=0, microsecond=0)
        t_close_dt = now_eg.replace(hour=h2, minute=m2, second=0, microsecond=0)

        if t_open_dt <= now_eg:
            await apply_status(context.bot, update.effective_chat.id, "open")
            msg = "🔓 فتح فوري (الموعد حان)."
        else:
            context.job_queue.run_once(job_trigger, when=t_open_dt, data=(update.effective_chat.id, "open", False))
            msg = f"✅ ميعاد فتح: {context.args[0]}"

        context.job_queue.run_once(job_trigger, when=t_close_dt, data=(update.effective_chat.id, "close", False))
        await update.message.reply_text(f"{msg}\n🔒 ميعاد قفل: {context.args[1]}")
    except: pass

async def open_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update): return
    await apply_status(context.bot, update.effective_chat.id, "open")

async def close_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update): return
    await apply_status(context.bot, update.effective_chat.id, "close")

# ---------------- تشغيل السيستم ----------------

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    jq = app.job_queue

    # برمجة المواعيد (تعديل الاختبار للنهاردة بس)
    for gid in GROUP_IDS:
        test_schedule = [
            ((8,0), "open"), ((8,15), "close"), 
            ((8,45), "open"), ((9,0), "close"), 
            ((23,40), "open"), ((23,45), "close"), # الميعاد الليلي المعدل 1
            ((0,5), "open"), ((0,10), "close")    # الميعاد الليلي المعدل 2
        ]
        for t, act in test_schedule:
            jq.run_daily(job_trigger, time=time(t[0], t[1], tzinfo=MY_TZ), data=(gid, act, True))

    app.add_handler(CommandHandler("open_now", open_now))
    app.add_handler(CommandHandler("close_now", close_now))
    app.add_handler(CommandHandler("addtime", addtime))
    
    print("🚀 وضع الاختبار يعمل.. الـ ID الجديد مضاف.. الجمعة مفعلة.. المواعيد الليلية معدلة.")
    app.run_polling()

if __name__ == "__main__":
    main()
