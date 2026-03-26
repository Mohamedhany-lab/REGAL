import logging
import pytz
from datetime import time
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# التوقيت
MY_TZ = pytz.timezone('Africa/Cairo') 

logging.basicConfig(level=logging.INFO)
TOKEN = "8685861366:AAFKP3Nm1RG8wVx4k0aQf1KKEneCXf22ja8"

# ---------------- الدالة المنقذة ----------------
async def set_group_status(context, chat_id, is_open):
    """
    هنا الحل: بنبعت الصلاحية الأساسية 'can_send_messages' 
    والتليجرام بيفهم الباقي تلقائياً في الإصدارات الجديدة
    """
    if is_open:
        # فتح كل حاجة
        perms = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_add_web_page_previews=True,
            can_send_other_messages=True
        )
    else:
        # قفل الرسائل (لما تقفل دي الباقي بيتقفل أوتوماتيك)
        perms = ChatPermissions(can_send_messages=False)
        
    return await context.bot.set_chat_permissions(chat_id=chat_id, permissions=perms)

# ---------------- الأوامر ----------------

async def close_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await set_group_status(context, update.effective_chat.id, False)
        await update.message.reply_text("🔒 خلاص يا ريس الجروب اتقفل.")
    except Exception as e:
        await update.message.reply_text(f"❌ ايرور جديد: {e}")

async def open_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await set_group_status(context, update.effective_chat.id, True)
        await update.message.reply_text("🔓 الجروب اتفتح، خليهم يهيصوا.")
    except Exception as e:
        await update.message.reply_text(f"❌ ايرور جديد: {e}")

# (باقي دوال addtime و main زي ما هي بس استبدل set_group_status)
async def scheduled_task(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id, action = job.data
    await set_group_status(context, chat_id, (action == "open"))

async def addtime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if len(context.args) < 2:
        await update.message.reply_text("استخدم: /addtime 22:00 close")
        return
    try:
        h, m = map(int, context.args[0].split(':'))
        action = context.args[1].lower()
        job_name = f"{chat_id}_{action}"
        for job in context.job_queue.get_jobs_by_name(job_name): job.schedule_removal()
        context.job_queue.run_daily(scheduled_task, time=time(h, m, tzinfo=MY_TZ), data=(chat_id, action), name=job_name)
        await update.message.reply_text(f"✅ تم الجدولة: {action} الساعة {context.args[0]}")
    except:
        await update.message.reply_text("فيه حاجة غلط في الوقت!")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("addtime", addtime))
    app.add_handler(CommandHandler("open_now", open_now))
    app.add_handler(CommandHandler("close_now", close_now))
    app.run_polling()

if __name__ == "__main__":
    main()
