import logging
import pytz
from datetime import time
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# التوقيت
MY_TZ = pytz.timezone('Africa/Cairo') 

logging.basicConfig(level=logging.INFO)
TOKEN = "8685861366:AAFKP3Nm1RG8wVx4k0aQf1KKEneCXf22ja8"

async def set_group_status(context, chat_id, is_open):
    # الطريقة دي بتشتغل مع كل الإصدارات بدون إيرور
    perms = ChatPermissions(can_send_messages=is_open)
    return await context.bot.set_chat_permissions(chat_id=chat_id, permissions=perms)

async def close_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_group_status(context, update.effective_chat.id, False)
    await update.message.reply_text("🔒 تم القفل بنجاح.")

async def open_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_group_status(context, update.effective_chat.id, True)
    await update.message.reply_text("🔓 تم الفتح بنجاح.")

async def addtime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        h, m = map(int, context.args[0].split(':'))
        action = context.args[1].lower()
        target_time = time(hour=h, minute=m, tzinfo=MY_TZ)
        
        context.job_queue.run_daily(
            lambda ctx: set_group_status(ctx, update.effective_chat.id, (action == "open")),
            time=target_time,
            name=f"{update.effective_chat.id}_{action}"
        )
        await update.message.reply_text(f"✅ جاهز! هعمل {action} الساعة {context.args[0]}")
    except:
        await update.message.reply_text("❌ اكتب الوقت صح كدة 22:00")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("addtime", addtime))
    app.add_handler(CommandHandler("open_now", open_now))
    app.add_handler(CommandHandler("close_now", close_now))
    print("البوت بيقوم اهو...")
    app.run_polling()
