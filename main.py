import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("8091015409:AAEq1Q2T2YeH83ku-DYJMxcdisdXGtEtEaM")

async def approve_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.chat_join_request.chat.id
    user_id = update.chat_join_request.from_user.id
    await context.bot.approve_chat_join_request(chat_id, user_id)
    logging.info(f"Approved join request from user {user_id}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(ChatJoinRequestHandler(approve_join))

if __name__ == '__main__':
    app.run_polling()

