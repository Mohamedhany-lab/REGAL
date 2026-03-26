import logging
import pytz
from datetime import time
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 1. إعدادات المنطقة الزمنية
MY_TZ = pytz.timezone('Africa/Cairo')

logging.basicConfig(level=logging.INFO)
TOKEN = "8685861366:AAFKP3Nm1RG8wVx4k0aQf1KKEneCXf22ja8"

# ---------------- دالة التحكم ----------------
async def set_group_status(context, chat_id, is_open):
    # في الإصدارات الجديدة، بنكتفي بـ can_send_messages
    # والبوت بيفهم الباقي أوتوماتيك
    perms = ChatPermissions(can_send_messages=is_open)
    return await context.bot.set_chat_permissions(chat_id=chat_id, permissions=perms)

# ---------------- أوامر الاختبار الفوري ----------------

async def close_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await set_group_status(context, update.effective_chat.id, False)
        await update.message.reply_text("🔒 تم القفل بنجاح!")
    except Exception as e:
        await update.message.reply_text(f"❌ ايرور في القفل: {e}")

async def open_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await set_group_status(context, update.effective_chat.id, True)
        await update.message.reply_text("🔓 تم الفتح بنجاح!")
    except Exception as e:
        await update.message.reply_text(f"❌ ايرور في الفتح: {e}")

# ---------------- الوظيفة المجدولة ----------------

async def scheduled_task(context: ContextTypes.DEFAULT_TYPE):
    # الداتا بتتبعت هنا من الـ Job Queue
    chat_id, action = context.job.data
    is_open = (action == "open")
    await set_group_status(context, chat_id, is_open)

# ---------------- أمر ضبط الموعد ----------------

async def addtime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ اكتب كدة:\n/addtime 22:00 close")
        return

    try:
        time_input = context.args[0]
        action = context.args[1].lower()
        
        # التأكد من التنسيق (HH:MM)
        h, m = map(int, time_input.split(':'))
        target_time = time(hour=h, minute=m, tzinfo=MY_TZ)

        # اسم فريد للمهمة
        job_name = f"{chat_id}_{action}"

        # مسح المهام القديمة لنفس النوع
        current_jobs = context.job_queue.get_jobs_by_name(job_name)
        for job in current_jobs:
            job.schedule_removal()

        # إضافة المهمة للجدول
        context.job_queue.run_daily(
            scheduled_task,
            time=target_time,
            data=(chat_id, action),
            name=job_name
        )
        await update.message.reply_text(f"✅ تم! الجروب هيعمل {action} يومياً الساعة {time_input}")

    except Exception as e:
        await update.message.reply_text(f"❌ خطأ حقيقي: {str(e)}")

# ---------------- تشغيل البوت ----------------

def main():
    # مهم جداً: الـ JobQueue بيحتاج يتفعل
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("addtime", addtime))
    app.add_handler(CommandHandler("open_now", open_now))
    app.add_handler(CommandHandler("close_now", close_now))

    print("البوت بدأ يشتغل...")
    app.run_polling()

if __name__ == "__main__":
    main()
