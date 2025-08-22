import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8091015409:AAEq1Q2T2YeH83ku-DYJMxcdisdXGtEtEaM"  # Replace with your bot token

async def approve_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.chat_join_request.chat.id
        user_id = update.chat_join_request.from_user.id
        await context.bot.approve_chat_join_request(chat_id, user_id)
        logger.info(f"Approved join request from user {user_id}")
    except Exception as e:
        logger.error(f"Error approving join request: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(ChatJoinRequestHandler(approve_join))
    app.run_polling()
