import json

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from advisor import analyze_job_offer_against_cv
from cv_evaluator import evaluate_cv_quality
from knowledge import ingest_to_knowledge_base, retrieve_from_knowledge_base
from writing_cv import generate_cv

start_keyboard = ReplyKeyboardMarkup([['/start']], resize_keyboard=True)
generate_keyboard = ReplyKeyboardMarkup([['/generate_cv']], resize_keyboard=True)

# Simple per-user state machine
user_states = json.load(open('data/user_states.json'))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! I'm your Career Advisor Bot.\n\n"
        "Send me your CV (as plain text), and then the job offer you'd like to evaluate.",
    )
    user_states[update.effective_user.id] = {"state": "expecting_cv"}


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in user_states:
        user_states[user_id] = {"state": "expecting_cv"}

    state = user_states[user_id]["state"]

    if state == "expecting_cv":
        print('📄 CV received.')
        await update.message.reply_text("📄 CV received. Embedding and storing...")
        ingest_to_knowledge_base(text, user_id)
        user_states[user_id]["state"] = "expecting_offer"
        await update.message.reply_text("✅ CV stored. Now send me the job offer you'd like to evaluate.")
    elif state == "expecting_offer":
        print('🤖 Analyzing job offer')
        await update.message.reply_text("🤖 Analyzing job offer against your CV...")
        result = retrieve_from_knowledge_base(text, user_id)
        await update.message.reply_text(f"📊 Match Analysis:\n\n{result}")
        user_states[user_id]["state"] = "expecting_offer"
    else:
        await update.message.reply_text("❓ Unexpected input. Please send /start to begin again.")

async def generate_cv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    job_description = " ".join(context.args)  # e.g., /generate_cv <job description>
    if not job_description:
        await update.message.reply_text("Please provide a job description after the command.")
        return
    print('📝 Generating CV')
    await update.message.reply_text("📝 Generating CV for your job description...")
    cv_text = generate_cv(job_description, user_id)
    await update.message.reply_text(f"📄 Generated CV:\n\n{cv_text}")
    print('🔍 Evaluating CV')
    await update.message.reply_text("🔍 Evaluating CV quality...")
    evaluation = evaluate_cv_quality(cv_text)
    await update.message.reply_text(f"✅ CV Quality Evaluation:\n\n{evaluation}")
