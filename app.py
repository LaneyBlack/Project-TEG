import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram_handler import start, handle_message, generate_cv_command, clear_embeddings_command, insert_job_command, \
    find_job_command, handle_job_selection

load_dotenv()

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate_cv", generate_cv_command))
    app.add_handler(CommandHandler("clear_embeddings", clear_embeddings_command))
    app.add_handler(CommandHandler("insert_job", insert_job_command))
    app.add_handler(CommandHandler("find_job", find_job_command))
    # Handler for job selection (numbers 1-5 and 'More')
    app.add_handler(MessageHandler(filters.Regex(r"^(1|2|3|4|5|More)$"), handle_job_selection))
    # General message handler (CV, job offer, etc.)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()