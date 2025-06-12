import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram_handler import start, handle_message, generate_cv_command

load_dotenv()

LANGSMITH_API_KEY=os.environ.get("LANGSMITH_API_KEY")
LANGSMITH_PROJECT=os.environ.get("LANGSMITH_PROJECT")
print(LANGSMITH_API_KEY)
print(LANGSMITH_PROJECT)
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("generate_cv", generate_cv_command))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()