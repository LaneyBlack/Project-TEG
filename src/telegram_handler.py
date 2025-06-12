import json
import os

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes

from advisor import get_job_offers_cv
from cv_evaluator import evaluate_cv_quality
from knowledge import ingest_to_knowledge_base, delete_user_embeddings
from writing_cv import generate_cv, create_pdf_from_text

# Simple per-user state machine
USER_STATES_PATH = 'data/user_states.json'
if os.path.exists(USER_STATES_PATH):
    user_states = json.load(open(USER_STATES_PATH))
else:
    user_states = {}


def save_user_states():
    with open(USER_STATES_PATH, 'w') as f:
        json.dump(user_states, f)


base_dir = os.path.dirname(os.path.dirname(__file__))

# Telegram Keyboards
main_keyboard = ReplyKeyboardMarkup(
    [['/generate_cv', '/write_cv'], ['/find_job', '/insert_job'], ['/clear_embeddings']],
    resize_keyboard=True
)
start_keyboard = ReplyKeyboardMarkup([['/start']], resize_keyboard=True)
generate_keyboard = ReplyKeyboardMarkup([['/generate_cv']], resize_keyboard=True)


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
        # update.message.reply_text(reply_markup=start_keyboard)
        user_states[user_id] = {"state": "expecting_cv"}

    state = user_states[user_id].get("state", "expecting_cv")

    if state == "expecting_cv":
        await update.message.reply_text("📄 CV received. Embedding and storing...")
        ingest_to_knowledge_base(text, user_id)
        user_states[user_id]["state"] = "expecting_job_mode"
        save_user_states()
        await update.message.reply_text(
            "✅ CV stored.\n\nWould you like to insert a job offer or find a job?",
            reply_markup=ReplyKeyboardMarkup([['/insert_job', '/find_job']], resize_keyboard=True)
        )
    elif state == "expecting_job_offer":
        await update.message.reply_text("🤖 Analyzing job offer and storing as active job...")
        # Insert offer
        ingest_to_knowledge_base(text, 'offers')
        user_states[user_id]["active_job"] = text
        user_states[user_id]["state"] = "ready"
        save_user_states()
        await update.message.reply_text(
            "✅ Job offer stored. You can now generate a tailored CV.",
            reply_markup=main_keyboard
        )
    elif state == "ready":
        await update.message.reply_text(
            "📝 You can use the buttons below to generate a CV, clear your data, or add/find another job.",
            reply_markup=main_keyboard
        )
    elif state == "expecting_job_title":
        await update.message.reply_text("🔍 Looking for job offers...")
        job_title = text
        jobs = get_job_offers_cv(job_title)
        if len(jobs) < 50:
            await update.message.reply_text("No jobs found for that title. Try another one.")
            return
        await update.message.reply_text(jobs, reply_markup=main_keyboard)
        user_states[user_id]["state"] = "ready"
        save_user_states()
    else:
        await update.message.reply_text(
            "❓ Unexpected input. Please send /start to begin again.",
            reply_markup=ReplyKeyboardRemove()
        )


async def write_cv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_states.get(user_id, {}).get("state", "")
    active_job = user_states.get(user_id, {}).get("active_job")
    if not active_job:
        await update.message.reply_text("No job offer selected. Please insert or find a job first.")
        return
    cv_text = generate_cv(active_job, user_id)

    scoring = 0
    retries = 3
    evaluation_string = ""
    while scoring < 8 or retries < 0:
        await update.message.reply_text("📝 Generating CV for your selected job...")
        cv_text = generate_cv(active_job, user_id, additional_comments=evaluation_string)

        await update.message.reply_text("🔍 Evaluating CV quality...")
        result = evaluate_cv_quality(cv_text)
        if not result.get('score', False):
            break
        evaluation_string += result['details']
        scoring = result['score']
        await update.message.reply_text(f"✅ CV Quality Evaluation:\n{result['score']}")
        retries -= 1

    await update.message.reply_text(f"📄 Generated CV:\n\n{cv_text}",
                                    reply_markup=main_keyboard)
    user_states[user_id]["cv"] = cv_text
    user_states[user_id]["state"] = "ready"


async def clear_embeddings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    delete_user_embeddings(user_id)
    user_states[user_id] = {"state": "expecting_cv"}
    save_user_states()
    await update.message.reply_text(
        "🧹 Your data has been cleared. Please send your CV to start again.",
        reply_markup=ReplyKeyboardRemove()
    )


async def insert_job_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id]["state"] = "expecting_job_offer"
    save_user_states()
    await update.message.reply_text(
        "Please paste the job offer you'd like to use.",
        reply_markup=ReplyKeyboardRemove()
    )


async def find_job_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id]["state"] = "expecting_job_title"
    save_user_states()
    await update.message.reply_text(
        "Please insert the job title you are looking for:",
        reply_markup=ReplyKeyboardRemove()
    )


# async def send_job_offers(update, jobs):
#     for idx, job in enumerate(jobs, 1):
#         # Customize this formatting as needed
#         text = f"{idx}. {job}"
#         await update.message.reply_text(text)


async def generate_cv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_states[user_id].get('cv', False):
        cv_text = generate_cv(user_states[user_id]['active_job'], user_id)
    cv_text = user_states[user_id]['cv']  # Replace with actual CV text retrieval logic

    base_dir = os.path.dirname(os.path.dirname(__file__))
    wkhtmltopdf_path = os.path.join(base_dir, "wkhtmltopdf", "bin", "wkhtmltopdf.exe")
    md_path = f"data/cv_{user_id}.md"
    pdf_path = f"data/cv_{user_id}.pdf"

    # Generate the PDF
    pdf_file = create_pdf_from_text(
        text=cv_text,
        md_path=md_path,
        pdf_path=pdf_path,
        wkhtmltopdf_path=wkhtmltopdf_path
    )

    # Send the PDF to the user
    with open(pdf_file, "rb") as pdf:
        await update.message.reply_document(document=pdf, filename="CV.pdf")
