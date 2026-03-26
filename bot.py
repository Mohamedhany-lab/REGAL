from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, time as dtime
import pytz
import logging

# ---------------- LOGGING ----------------
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ---------------- TOKEN ----------------
TOKEN = "8685861366:AAFKP3Nm1RG8wVx4k0aQf1KKEneCXf22ja8"

# ---------------- TIMEZONE ----------------
egypt_tz = pytz.timezone("Africa/Cairo")


# ---------------- GROUP ACTIONS ----------------
async def close_group(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data
    try:
        await context.bot.set_chat_permissions(
            chat_id=chat_id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        logging.info(f"Closed group {chat_id}")
    except Exception as e:
        logging.error(e)


async def open_group(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data
    try:
        await context.bot.set_chat_permissions(
            chat_id=chat_id,
            permissions=ChatPermissions(can_send_messages=True)
        )
        logging.info(f"Opened group {chat_id}")
    except Exception as e:
        logging.error(e)


# ---------------- CLEAN OLD JOBS ----------------
def remove_jobs(job_queue, name):
    jobs = job_queue.get_jobs_by_name(name)
    for j in jobs:
        j.schedule_removal()


# ---------------- ADD TIME COMMAND ----------------
async def addtime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        job_queue = context.job_queue

        if len(context.args) < 2:
            await update.message.reply_text("Usage: /addtime HH:MM close/open")
            return

        time_str = context.args[0]
        action = context.args[1].lower()

        hour, minute = map(int, time_str.split(":"))

        now = datetime.now(egypt_tz)

        target_dt = egypt_tz.localize(
            datetime(now.year, now.month, now.day, hour, minute)
        )

        # لو الوقت عدّى، خليه بكرة
        if target_dt < now:
            target_dt = target_dt.replace(day=now.day + 1)

        remove_jobs(job_queue, str(chat_id))

        if action == "close":
            job_queue.run_once(
                close_group,
                when=target_dt,
                data=chat_id,
                name=str(chat_id)
            )

        elif action == "open":
            job_queue.run_once(
                open_group,
                when=target_dt,
                data=chat_id,
                name=str(chat_id)
            )

        else:
            await update.message.reply_text("Use open or close only")
            return

        await update.message.reply_text("✔️ تم الضبط بتوقيت مصر بنجاح")

    except Exception as e:
        logging.error(e)
        await update.message.reply_text("حصل خطأ — راجع الأمر")


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is running 👌")


# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addtime", addtime))

    logging.info("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
