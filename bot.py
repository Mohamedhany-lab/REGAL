import logging
import pytz
from datetime import time
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# إعداد التوقيت
MY_TZ = pytz.timezone('Africa/Cairo') 

logging.basicConfig(level=logging.INFO)
TOKEN = "8685861366:AAFKP3Nm1RG8wVx4k0aQf1KKEneCXf22ja8"

# ---------------- الدالة المنقذة (تعديل الأرجومنتات) ----------------
async def set_group_status(context, chat_id, is_open):
    if is_open:
        # في الإصدارات الجديدة، بنستخدم can_send_messages 
        # والباقي بيفتح معاه، أو بنسيبها فاضية للأدمن يحددها
        perms = ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_voice_notes=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
    else:
        # قفل الرسائل بيقفل كل حاجة تانية أوتوماتيك
        perms = ChatPermissions(can_send_messages=False)
        
    return await context.bot.set_chat_permissions(chat_id=chat_id, permissions=perms)

# ---------------- الأوامر ----------------

async def close_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await set_group_status(context, update.effective_chat.id, False)
        await update.message.reply_text("🔒 تم قفل الجروب فوراً.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ في القفل: {e}")

async def open_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await set_group_status(context, update.effective_chat.id, True)
        await update.message.reply_text("🔓 تم فتح الجروب فوراً.")
    except Exception as e:
        # لو الإيرور لسه موجود، هنستخدم أقل عدد ممكن من الـ Arguments
        try:
            perms = ChatPermissions(can_send_messages=True)
            await context.bot.set_chat_permissions(chat_id=update.effective_chat.id, permissions=perms)
            await update.message.reply_text("🔓 تم الفتح (بإعدادات محدودة).")
        except Exception as e2:
            await update.message.reply_text(f"❌ خطأ نهائي: {e2}")

async def scheduled_task(context: ContextTypes.DEFAULT_TYPE):
    chat_id, action = context.job.data
    await set_group_status(context, chat_id, (action == "open"))

async def addtime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ المثال: /addtime 22:00 close")
        return
    
    try:
        time_str = context.args[0] # HH:MM
        action = context.args[1].lower() # open or close
        
        h, m = map(int, time_str.split(':'))
        target_time = time(hour=h, minute=m, tzinfo=MY_TZ)
        
        job_name = f"{update.effective_chat.id}_{action}"
        
        # مسح القديم
        for job in context.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()
            
        context.job_queue.run_daily(
            scheduled_task, 
            time=target_time, 
            data=(update.effective_chat.id, action), 
            name=job_name
        )
        await update.message.reply_text(f"✅ تم جدولة {action} يومياً الساعة {time_str}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ في التنفيذ: {e}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("addtime", addtime))
    app.add_handler(CommandHandler("open_now", open_now))
    app.add_handler(CommandHandler("close_now", close_now))
    app.run_polling()

if __name__ == "__main__":
    main()
