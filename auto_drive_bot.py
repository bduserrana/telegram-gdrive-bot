import os
import re
import subprocess
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Loaded from environment on Render
DOWNLOAD_DIR = "downloads"

def extract_folder_id(text):
    match = re.search(r'folders/([a-zA-Z0-9_-]+)', text)
    return match.group(1) if match else None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    chat_id = update.message.chat.id

    folder_id = extract_folder_id(message)
    if not folder_id:
        await update.message.reply_text("❌ Please send a valid Google Drive folder link.")
        return

    folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
    await update.message.reply_text("📥 Downloading files from Google Drive...")

    try:
        subprocess.run(["gdown", "--folder", folder_url, "--output", DOWNLOAD_DIR], check=True)

        folder_path = os.path.join(DOWNLOAD_DIR, folder_id)
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    await context.bot.send_document(chat_id=chat_id, document=f)
        await update.message.reply_text("✅ All files sent!")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot is running. Send it a Google Drive folder link...")
    application.run_polling()

if __name__ == '__main__':
    main()
