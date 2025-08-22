import io
import os
import threading
import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, ChatJoinRequestHandler,
    ContextTypes,
)
from dotenv import load_dotenv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, green

# ─── LOAD ENV ────────────────────────────────────────────────
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_LINK = os.getenv("CHANNEL_LINK")
ADMIN_ID = 7677825556

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
        "",
        "- All content, tools, and videos shared by @SecureX_Tools are strictly for educational and ethical",
        "  cybersecurity purposes.",
        "- You agree not to use any information for illegal hacking, unauthorized access, or unlawful activity.",
        "- You take full responsibility for how you use the knowledge and resources provided.",
        "- These materials are intended to raise awareness and educate about cybersecurity, ethical hacking,",
        "  and digital protection.",
        "- The creator of @SecureX_Tools is not responsible for any misuse or illegal activity.",
        "- The owner of the @SecureX_Tools channel is also not responsible for any user actions or content misuse.",
        "- If anyone chooses to misuse the content for illegal activity, they do so at their own risk.",
        "  The @SecureX_Tools channel and its owner are not responsible for any such actions.",
        "- No support will be provided for criminal intent or abuse of shared content.",
        "",
        "⚠️ Misuse may lead to legal action or a permanent ban.",
        "",
        "📩 Message to Telegram & Channel Moderators",
        "If you have any concerns regarding the content shared by @SecureX_Tools, please contact me directly",
        "before taking any action.",
        "Email: securexofficel@gmail.com",
        "All content is strictly for educational purposes only. Please avoid removing or reporting the",
        "channel without first reaching out.",
        "",
        "✅ Digital Proof of Consent",
        f"Accepted by Telegram User ID: {user_id}",
        f"Username: @{username}",
        f"Full Name: {full_name}",
        "This log serves as your digital signature.",
        "",
        "🔒 Channel & Ownership Verification",
        "- Channel Name: @SecureX_Tools",
        "- Channel Owner Telegram ID: 7677825556",
        "- This agreement is verified and issued by the owner of @SecureX_Tools.",
        "- All legal responsibility for sharing and managing content belongs solely to the user,",
        "  not the channel or its owner."
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

# ─── MEMORY ──────────────────────────────────────────────────
agreed_users = set()
rejected_users = set()

# ─── FLASK ───────────────────────────────────────────────────
app = Flask(__name__)
@app.route("/")
def home():
    return "🤖 Bot is alive!"
def run_flask():
    app.run(host="0.0.0.0", port=8080)

# ─── /start ──────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    username = user.username or f"user_{user.id}"
    full_name = f"{user.first_name} {user.last_name or ''}".strip()

    terms = (
        "<b>📜 Terms & Conditions</b>\n\n"
        "By continuing, you confirm that:\n\n"
        "• All content, tools, and videos shared by @SecureX_Tools are strictly for educational and ethical cybersecurity purposes.\n"
        "• You agree not to use any information for illegal hacking, unauthorized access, or unlawful activity.\n"
        "• You take full responsibility for how you use the knowledge and resources provided.\n"
        "• These materials are intended to raise awareness and educate about cybersecurity, ethical hacking, and digital protection.\n"
        "• The creator of @SecureX_Tools is not responsible for any misuse or illegal activity.\n"
        "• The owner of the @SecureX_Tools channel is also not responsible for any user actions or content misuse.\n"
        "• If anyone chooses to misuse the content for illegal activity, they do so at their own risk. The @SecureX_Tools channel and its owner are not responsible for any such actions.\n"
        "• No support will be provided for criminal intent or abuse of shared content.\n\n"
        "⚠️ Misuse may lead to legal action or a permanent ban.\n\n"
        "<b>📩 Contact Moderators</b>\n"
        "Email: securexofficel@gmail.com\n"
    )

    if user_id in agreed_users:
        await update.message.reply_text(
            "✅ You have already accepted the Terms & Conditions.\nYou may now request access to the channel if needed.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📥 Join Channel", url=CHANNEL_LINK)]
            ])
        )
    elif user_id in rejected_users:
        await update.message.reply_text(
            "❌ You previously rejected the Terms & Conditions.\nYou cannot access the channel unless you accept the rules. Contact admin if you made a mistake."
        )
    else:
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Accept", callback_data="accept")],
            [InlineKeyboardButton("❌ Reject", callback_data="reject")]
        ])
        await update.message.reply_text(terms + "\n\n🔐 Please accept or reject to continue.", reply_markup=buttons, parse_mode="HTML")

# ─── BUTTON HANDLER ──────────────────────────────────────────
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
        await context.bot.send_document(
            chat_id=ADMIN_ID,
            document=InputFile(pdf_buffer, filename=f"Agreement_{user_id}.pdf"),
            caption=f"📄 Agreement by @{username} ({user_id})"
        )

        await query.edit_message_text(
            "✅ Thank you! Tap below to join the channel.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📥 Join Channel", url=CHANNEL_LINK)]
            ])
        )

    elif query.data == "reject":
        rejected_users.add(user_id)
        log_entry = format_user_log(user_id, username, full_name, "REJECT")
        save_to_file(REJECTED_FILE, log_entry)

        await context.bot.send_message(ADMIN_ID, f"❌ @{username} ({user_id}) rejected the agreement.")
        await query.edit_message_text("❌ You rejected the terms. Access denied.")

# ─── JOIN REQUEST ────────────────────────────────────────────
async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    user_id = str(user.id)
    username = user.username or f"user_{user.id}"
    full_name = f"{user.first_name} {user.last_name or ''}".strip()

    if user_id in agreed_users:
        try:
            await update.chat_join_request.approve()
            await context.bot.send_message(
                chat_id=user.id,
                text="🎉 You’ve been approved! Welcome.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🟢 Open Channel", url=CHANNEL_LINK)]
                ])
            )
        except Exception as e:
            print(f"❌ Approve error: {e}")
    else:
        try:
            await update.chat_join_request.decline()
            await context.bot.send_message(
                chat_id=user.id,
                text="🚫 Access Denied.\nUse /start to accept the rules before joining."
            )
        except Exception as e:
            print(f"❌ Decline error: {e}")

# ─── BOT RUN ─────────────────────────────────────────────────
def run_bot():
    if not BOT_TOKEN:
        raise RuntimeError("❌ BOT_TOKEN not set in .env")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    print("✅ Bot is running...")
    app.run_polling()

# ─── MAIN ────────────────────────────────────────────────────
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
