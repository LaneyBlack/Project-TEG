from telegram import Update
from telegram.ext import ContextTypes
from advisor import analyze_job_offer_against_cv
from knowledge import ingest_to_knowledge_base

# Simple per-user state machine
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! I'm your Career Advisor Bot.\n\n"
        "Send me your CV (as plain text), and then the job offer you'd like to evaluate."
    )
    user_states[update.effective_user.id] = {"state": "expecting_cv"}


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in user_states:
        user_states[user_id] = {"state": "expecting_cv"}

    state = user_states[user_id]["state"]

    if state == "expecting_cv":
        # Store the CV
        await update.message.reply_text("📄 CV received. Embedding and storing...")
        ingest_to_knowledge_base(text, user_id)
        user_states[user_id]["state"] = "expecting_offer"
        await update.message.reply_text("✅ CV stored. Now send me the job offer you'd like to evaluate.")
    elif state == "expecting_offer":
        await update.message.reply_text("🤖 Analyzing job offer against your CV...")
        result = analyze_job_offer_against_cv(text)
        await update.message.reply_text(f"📊 Match Analysis:\n\n{result}")
        user_states[user_id]["state"] = "expecting_offer"  # Allow multiple offers
    else:
        await update.message.reply_text("❓ Unexpected input. Please send /start to begin again.")
