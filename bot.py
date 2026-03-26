from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging

logging.basicConfig(level=logging.INFO)

TOKEN = "8685861366:AAFKP3Nm1RG8wVx4k0aQf1KKEneCXf22ja8"


async def close_group(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data
    await context.bot.set_chat_permissions(
        chat_id=chat_id,
        permissions=ChatPermissions(can_send_messages=False)
    )


async def open_group(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data
    await context.bot.set_chat_permissions(
        chat_id=chat_id,
        permissions=ChatPermissions(can_send_messages=True)
    )


def remove_jobs(job_queue, name):
    for job in job_queue.get_jobs_by_name(name):
        job.schedule_removal()


async def addtime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        job_queue = context.job_queue

        if len(context.args) < 2:
            await update.message.reply_text("Use /addtime HH:MM close/open")
            return

        hour, minute = map(int, context.args[0].split(":"))
        action = context.args[1].lower()

        remove_jobs(job_queue, str(chat_id))

        if action == "close":
            job_queue.run_daily(
                close_group,
                time=(hour, minute),
                days=(0,1,2,3,4,5,6),
                data=chat_id,
                name=str(chat_id)
            )

        elif action == "open":
            job_queue.run_daily(
                open_group,
                time=(hour, minute),
                days=(0,1,2,3,4,5,6),
                data=chat_id,
                name=str(chat_id)
            )

        else:
            await update.message.reply_text("use open or close")
            return

        await update.message.reply_text("✔️ تم الضبط يوميًا بنجاح")

    except Exception as e:
        logging.error(e)
        await update.message.reply_text("error in command")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("addtime", addtime))

    app.run_polling()


if __name__ == "__main__":
    main()
