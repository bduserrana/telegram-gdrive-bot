# =============================================================
# Telegram Google Drive Folder Downloader Bot
# Copyright © 2024 𝙼𝚁. 𝙿𝚁𝙾𝙵𝙴𝚂𝚂𝙾𝚁 — https://t.me/formsgadmin
# =============================================================

import os
import re
import subprocess
import logging
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from flask import Flask
import threading

# === Configuration ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
DOWNLOAD_DIR = "downloads"
LOG_FILE = "bot.log"

# === Set up logging ===
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# === Flask web server ===
app = Flask(__name__)

@app.route('/')
def status():
    return "🚀 Telegram Google Drive Bot is running! — © 𝙼𝚁. 𝙿𝚁𝙾𝙵𝙴𝚂𝚂𝙾𝚁"

def start_web_ui():
    app.run(host='0.0.0.0', port=10000)

# === Helper: Extract Google Drive folder ID ===
def extract_folder_id(text):
    match = re.search(r'folders/([a-zA-Z0-9_-]+)', text)
    return match.group(1) if match else None

# === Telegram bot handler ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    chat_id = update.message.chat.id

    folder_id = extract_folder_id(message)
    if not folder_id:
        await update.message.reply_text("❌ Please send a valid Google Drive folder link.")
        return

    folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
    await update.message.reply_text("📥 Downloading files from Google Drive...")
    logging.info(f"Received folder link: {folder_url} from chat_id: {chat_id}")

    try:
        subprocess.run(["gdown", "--folder", folder_url, "--output", DOWNLOAD_DIR], check=True)

        # Detect if content was saved as a folder or directly in DOWNLOAD_DIR
        downloaded_items = os.listdir(DOWNLOAD_DIR)
        if not downloaded_items:
            await update.message.reply_text("❌ Failed to download. Nothing found.")
            logging.error("Download directory is empty.")
            return

        first_item = os.path.join(DOWNLOAD_DIR, downloaded_items[0])
        folder_path = first_item if os.path.isdir(first_item) else DOWNLOAD_DIR

        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

                if file_size_mb > 1995:
                    await context.bot.send_message(chat_id=chat_id, text=f"⚠️ Skipping '{filename}' — too large (>2GB)")
                    logging.warning(f"Skipped file {filename} — size: {file_size_mb:.2f}MB")
                    continue

                with open(file_path, 'rb') as f:
                    await context.bot.send_document(chat_id=chat_id, document=f)
                    logging.info(f"Sent file: {filename} to chat_id: {chat_id}")

        await update.message.reply_text("✅ All files sent!")
        subprocess.run(["rm", "-rf", folder_path])
        logging.info(f"Deleted folder: {folder_path}")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        logging.error(f"Error processing folder: {str(e)}")

# === Main Entry ===
def main():
    threading.Thread(target=start_web_ui, daemon=True).start()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot is running. Send it a Google Drive folder link...")
    application.run_polling()

if __name__ == '__main__':
    main()
