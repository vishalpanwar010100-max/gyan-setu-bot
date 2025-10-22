import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from telegram.helpers import escape_markdown
from datetime import datetime, timedelta
import logging

# -----------------------------
# CONFIG
# -----------------------------
BOT_TOKEN = os.environ.get("7803458221:AAH1JuQpJ1RR5ZtihC_3UUaF9l_ToqPCIyM")
ADMIN_CHAT_ID = 8064043725
UPLOAD_KEY = "admin000"

FAQ_QUESTIONS = {
    "time for homework demand": "You can demand homework at any time.",
    "when homework is uploaded to website or app": "Time: 7:00 to 8:00 PM."
}
WHATSAPP_CHANNEL = "https://whatsapp.com/channel/0029Vb7EwfHGk1FryYMPm33x"
MAX_QUESTIONS = 10

logging.basicConfig(level=logging.INFO)

# -----------------------------
# GLOBAL STATE
# -----------------------------
all_users = set()
user_waiting_for_update = set()
user_warnings = {}
blocked_users = {}
authorized_upload_users = {}
user_unusual_count = {}

# -----------------------------
# FLASK SERVER
# -----------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Gyan Setu Bot is alive on Render!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# -----------------------------
# HELPERS
# -----------------------------
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Website Link", callback_data="website")],
        [InlineKeyboardButton("📩 Demand Update", callback_data="update")],
        [InlineKeyboardButton("ℹ️ About Gyan Setu", callback_data="about")],
        [InlineKeyboardButton("📚 Homework", callback_data="homework")],
        [InlineKeyboardButton("❓ FAQ", callback_data="faq")]
    ])

def remaining_block_time(unblock_time):
    now = datetime.now()
    remaining = unblock_time - now
    if remaining.total_seconds() <= 0:
        return "0s"
    hours, remainder = divmod(int(remaining.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

# -----------------------------
# HANDLERS (copied from your bot)
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    all_users.add(user_id)
    text = "👋 Hi, welcome to Gyan Setu! What do you want me to do?"
    await update.message.reply_text(
        escape_markdown(text, version=2),
        reply_markup=main_menu_keyboard(),
        parse_mode="MarkdownV2"
    )

async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    authorized_upload_users[user_id] = {'state': 'awaiting_key'}
    await update.message.reply_text("🔑 Send the key to proceed with upload (any user with correct key can upload).")

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Only admin can use this command.")
        return
    if update.message.text.startswith("/users"):
        text = "👥 Users:\n"
        keyboard = []
        for uid in all_users:
            rem = remaining_block_time(blocked_users.get(uid, datetime.now())) if uid in blocked_users else "0s"
            text += f"{uid} - Block remaining: {rem}\n"
            buttons = [InlineKeyboardButton("Block", callback_data=f"block_{uid}"),
                       InlineKeyboardButton("Unblock", callback_data=f"unblock_{uid}")]
            keyboard.append(buttons)
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    now = datetime.now()

    if user_id in blocked_users:
        unblock_time = blocked_users[user_id]
        if now >= unblock_time:
            del blocked_users[user_id]
            user_warnings[user_id] = 0
            user_unusual_count[user_id] = 0
            await context.bot.send_message(chat_id=user_id, text="✅ Your 24-hour block expired.")
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"✅ User {user_id} unblocked.")
        else:
            rem = remaining_block_time(unblock_time)
            await query.answer(f"⛔ Blocked. Remaining: {rem}", show_alert=True)
            return

    if data == "website":
        await query.edit_message_text("🌐 Visit: [www.setugyan.live](https://www.setugyan.live)", parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]]))
    elif data == "update":
        user_waiting_for_update.add(user_id)
        await query.edit_message_text("📩 Type your update request below:",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]]))
    elif data == "about":
        await query.edit_message_text("ℹ️ *Gyan Setu* is an educational platform by *Team Hackers*.",
                                      parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]]))
    elif data == "main":
        await query.edit_message_text("👋 Hi, welcome back to Gyan Setu!", reply_markup=main_menu_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    all_users.add(user_id)
    now = datetime.now()
    text_lower = update.message.text.lower() if update.message.text else ""

    if user_id in blocked_users:
        unblock_time = blocked_users[user_id]
        if now >= unblock_time:
            del blocked_users[user_id]
            user_unusual_count[user_id] = 0
            await update.message.reply_text("✅ Block expired.")
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"✅ User {user_id} auto-unblocked.")
        else:
            rem = remaining_block_time(unblock_time)
            await update.message.reply_text(f"⛔ You are blocked. Remaining: {rem}")
            return

    if "gyan setu" in text_lower:
        await start(update, context)
        return

    if user_id in user_waiting_for_update:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"📩 Update from {user_id}: {update.message.text}")
        await update.message.reply_text("✅ Sent to admin.", reply_markup=main_menu_keyboard())
        user_waiting_for_update.remove(user_id)
        return

# -----------------------------
# MAIN
# -----------------------------
def main():
    threading.Thread(target=run_flask).start()
    app_tg = ApplicationBuilder().token(BOT_TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("users", admin_command))
    app_tg.add_handler(CommandHandler("upload", upload_command))
    app_tg.add_handler(CallbackQueryHandler(button_click))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Gyan Setu Bot running with Flask (Render-compatible)")
    app_tg.run_polling()

if __name__ == "__main__":
    main()
