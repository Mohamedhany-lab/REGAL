from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import datetime
import logging

logging.basicConfig(level=logging.INFO)

TOKEN = "8685861366:AAFKP3Nm1RG8wVx4k0aQf1KKEneCXf22ja8"

# تخزين المواعيد لكل جروب
groups = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("البوت شغال 👌")

async def close_group(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data
    try:
        await context.bot.set_chat_permissions(
            chat_id=chat_id,
            permissions=ChatPermissions(can_send_messages=False)
        )
    except Exception as e:
        logging.error(e)

async def open_group(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data
    try:
        await context.bot.set_chat_permissions(
            chat_id=chat_id,
            permissions=ChatPermissions(can_send_messages=True)
        )
    except Exception as e:
        logging.error(e)

async def addtime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        time_str = context.args[0]
        action = context.args[1].lower()

        hour, minute = map(int, time_str.split(":"))

        job_queue = context.application.job_queue

        if action == "close":
            job_queue.run_daily(
                close_group,
                time=datetime.time(hour, minute),
                data=chat_id
            )
        else:
            job_queue.run_daily(
                open_group,
                time=datetime.time(hour, minute),
                data=chat_id
            )

        await update.message.reply_text("تم الإضافة ✅")

    except Exception as e:
        logging.error(e)
        await update.message.reply_text("اكتب كده: /addtime 08:00 close")

app = ApplicationBuilder().token(TOKEN).job_queue(None).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addtime", addtime))

app.run_polling()
