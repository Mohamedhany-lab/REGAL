from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import datetime
import logging
from pytz import timezone

# ---------------- LOGGING ----------------
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = "PUT_YOUR_TOKEN_HERE"

# ---------------- TIMEZONE ----------------
egypt_tz = timezone("Africa/Cairo")

# ---------------- UTIL ----------------
def egypt_to_utc(hour, minute):
    """
    تحويل وقت مصر → UTC بشكل آمن 100%
    """
    now = datetime.datetime.utcnow()

    naive_dt = datetime.datetime(now.year, now.month, now.day, hour, minute)

    local_dt = egypt_tz.localize(naive_dt, is_dst=None)

    utc_dt = local_dt.astimezone(timezone("UTC"))

    return utc_dt.time()

# ---------------- ACTIONS ----------------
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

# ---------------- CLEAN DUPLICATES ----------------
def remove_existing_jobs(job_queue, chat_id):
    current_jobs = job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

# ---------------- ADD TIME ----------------
async def addtime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id

        if len(context.args) < 2:
            await update.message.reply_text("استخدم: /addtime 08:00 close")
            return

        time_str = context.args[0]
        action = context.args[1].lower()

        hour, minute = map(int, time_str.split(":"))

        job_queue = context.job_queue

        # 🟢 مهم: منع التكرار
        remove_existing_jobs(job_queue, chat_id)

        target_time = egypt_to_utc(hour, minute)

        if action == "close":
            job_queue.run_daily(
                close_group,
                time=target_time,
                data=chat_id,
                name=str(chat_id)
            )

        elif action == "open":
            job_queue.run_daily(
                open_group,
                time=target_time,
                data=chat_id,
                name=str(chat_id)
            )

        else:
            await update.message.reply_text("اكتب open أو close فقط")
            return

        await update.message.reply_text("✔️ تم الضبط بتوقيت مصر بنجاح")

    except Exception as e:
        logging.error(e)
        await update.message.reply_text("حصل خطأ — راجع الأمر")

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("البوت شغال 👌")

# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addtime", addtime))

    logging.info("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
