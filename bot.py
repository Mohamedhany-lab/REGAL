import logging
import pytz
from datetime import datetime, time
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 1. إعدادات التوقيت الصارمة (القاهرة)
MY_TZ = pytz.timezone('Africa/Cairo')

# 2. قائمة الـ 12 جروب المعتمدة
GROUP_IDS = [
    -1003870414631, -1003868568456, -1003843038200, -1003842260078,
    -1003773422592, -1003309198838, -1003544491812, -1003715228581,
    -1003304815564, -1003835237780, -1003851844806, -1003863374316
]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = "8685861366:AAFKP3Nm1RG8wVx4k0aQf1KKEneCXf22ja8"

# ---------------- وظائف التحقق والأمان ----------------

async def is_admin(update: Update):
    try:
        user_status = await update.effective_chat.get_member(update.effective_user.id)
        return user_status.status in ['administrator', 'creator']
    except: return False

async def set_group_status(context, chat_id, is_open):
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
        await context.bot.set_chat_permissions(chat_id=chat_id, permissions=perms)
    except Exception as e:
        logging.error(f"❌ خطأ في تنفيذ الصلاحيات للجروب {chat_id}: {e}")

# ---------------- المحركات المجدولة ----------------

async def fixed_scheduled_task(context: ContextTypes.DEFAULT_TYPE):
    """للمواعيد الثابتة: تحترم إجازة الثلاثاء والجمعة"""
    now_in_egypt = datetime.now(MY_TZ)
    if now_in_egypt.weekday() in [1, 4]: return # 1=Tue, 4=Fri
    chat_id, action = context.job.data
    await set_group_status(context, chat_id, (action == "open"))

async def extra_scheduled_task(context: ContextTypes.DEFAULT_TYPE):
    """للأوامر الإضافية: تعمل دوماً حتى في الإجازات"""
    chat_id, action = context.job.data
    await set_group_status(context, chat_id, (action == "open"))

# ---------------- الأوامر اليدوية (للأدمن فقط) ----------------

async def addtime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update): return
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ المثال: /addtime 14:00 14:15")
        return
    try:
        now = datetime.now(MY_TZ)
        h1, m1 = map(int, context.args[0].split(':'))
        h2, m2 = map(int, context.args[1].split(':'))
        
        t_open = now.replace(hour=h1, minute=m1, second=0, microsecond=0)
        t_close = now.replace(hour=h2, minute=m2, second=0, microsecond=0)

        # تحصين الفتح الفوري لو الميعاد "دلوقتي"
        if abs((now - t_open).total_seconds()) <= 60 or t_open < now:
            await set_group_status(context, update.effective_chat
