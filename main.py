import io
import os
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ChatJoinRequestHandler, ContextTypes
)
from dotenv import load_dotenv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, green

# ─── LOAD ENV ────────────────────────────────────────────────
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_LINK = os.getenv("CHANNEL_LINK")
ADMIN_ID = int(os.getenv("ADMIN_ID", 7677825556))

# ─── LOGGING ─────────────────────────────────────────────────
LOG_FOLDER = "Logs"
AGREE_FILE = os.path.join(LOG_FOLDER, "AGREE.txt")
REJECTED_FILE = os.path.join(LOG_FOLDER, "REJECTED.txt")
SEPARATOR = "-" * 120 + "\n"

def ensure_log_folder():
    os.makedirs(LOG_FOLDER, exist_ok=True)

def format_user_log(user_id, username, full_name, action):
    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    return f"{username}>| ID: {user_id} | Name: {full_name} | {timestamp} | Action: {action}\n{SEPARATOR}"

def save_to_file(file_path, text):
    ensure_log_folder()
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(text)

# ─── PDF GENERATOR ───────────────────────────────────────────
def generate_pdf_bytes(user_id, username, full_name):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 50, "🛡️ SecureX_Tools Agreement")
    text = c.beginText(40, height - 100)
    text.setFont("Helvetica", 11)
    lines = [
        "By continuing, you confirm that:",
        "- All content is for educational purposes.",
        "- You accept full responsibility for its use.",
        f"Accepted by Telegram User ID: {user_id}",
        f"Username: @{username}",
        f"Full Name: {full_name}"
    ]
    for line in lines:
        text.textLine(line)
    c.drawText(text)
    c.setFillColor(green)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, 60, "✔ AGREEMENT ACCEPTED")
    c.setFillColor(HexColor("#000000"))
    c.setFont("Helvetica", 10)
    c.drawString(40, 45, f"Signed on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.save()
    buffer.seek(0)
    return buffer

agreed_users = set()
rejected_users = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    username = user.username or f"user_{user.id}"
    full_name = f"{user.first_name} {user.last_name or ''}".strip()
    if user_id in agreed_users:
        await update.message.reply_text(
            "✅ Already accepted.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📥 Join Channel", url=CHANNEL_LINK)]])
        )
    elif user_id in rejected_users:
        await update.message.reply_text("❌ You rejected the Terms.")
    else:
        terms = "<b>📜 Terms & Conditions</b>\nAccept or reject to continue."
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Accept", callback_data="accept")],
            [InlineKeyboardButton("❌ Reject", callback_data="reject")]
        ])
        await update.message.reply_text(terms, reply_markup=buttons, parse_mode="HTML")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_id = str(user.id)
    username = user.username or f"user_{user.id}"
    full_name = f"{user.first_name} {user.last_name or ''}".strip()
    if query.data == "accept":
        agreed_users.add(user_id)
        log_entry = format_user_log(user_id, username, full_name, "AGREE")
        save_to_file(AGREE_FILE, log_entry)
        pdf_buffer = generate_pdf_bytes(user_id, username, full_name)
        await context.bot.send_document(chat_id=ADMIN_ID, document=InputFile(pdf_buffer, filename=f"Agreement_{user_id}.pdf"))
        await query.edit_message_text("✅ Accepted. Tap to join channel.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📥 Join Channel", url=CHANNEL_LINK)]]))
    elif query.data == "reject":
        rejected_users.add(user_id)
        save_to_file(REJECTED_FILE, format_user_log(user_id, username, full_name, "REJECT"))
        await query.edit_message_text("❌ Rejected.")

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    user_id = str(user.id)
    if user_id in agreed_users:
        await update.chat_join_request.approve()
    else:
        await update.chat_join_request.decline()

def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    run_bot()
