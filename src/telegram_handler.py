import json
import os

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from advisor import analyze_job_offer_against_cv, get_job_offers_cv
from cv_evaluator import evaluate_cv_quality
from knowledge import ingest_to_knowledge_base, retrieve_from_knowledge_base, delete_user_embeddings
from writing_cv import generate_cv

start_keyboard = ReplyKeyboardMarkup([['/start']], resize_keyboard=True)
generate_keyboard = ReplyKeyboardMarkup([['/generate_cv']], resize_keyboard=True)

# Simple per-user state machine
USER_STATES_PATH = 'data/user_states.json'
if os.path.exists(USER_STATES_PATH):
    user_states = json.load(open(USER_STATES_PATH))
else:
    user_states = {}

def save_user_states():
    with open(USER_STATES_PATH, 'w') as f:
        json.dump(user_states, f)

main_keyboard = ReplyKeyboardMarkup(
    [['/generate_cv', '/clear_embeddings'], ['/insert_job', '/find_job']],
    resize_keyboard=True
)
generate_keyboard = ReplyKeyboardMarkup([['/generate_cv']], resize_keyboard=True)

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
            "You can use the buttons below to generate a CV, clear your data, or add/find another job.",
            reply_markup=main_keyboard
        )

    elif state == "expecting_job_title":
        job_title = text
        jobs = get_job_offers_cv(job_title)  # Returns a list of job dicts
        if not jobs:
            await update.message.reply_text("No jobs found for that title. Try another one.")
            return
        user_states[user_id]["job_search_results"] = jobs
        user_states[user_id]["state"] = "expecting_job_selection"
        save_user_states()
        await send_job_offers(update, jobs)
    elif state == "expecting_job_selection":
        if text in ['1', '2', '3', '4', '5']:
            idx = int(text) - 1
            jobs = user_states[user_id].get("job_search_results", [])
            if 0 <= idx < len(jobs):
                user_states[user_id]["active_job"] = jobs[idx]["description"]
                user_states[user_id]["state"] = "ready"
                save_user_states()
                await update.message.reply_text(
                    f"✅ You selected: {jobs[idx]['title']}\nYou can now generate a tailored CV.",
                    reply_markup=main_keyboard
                )
            else:
                await update.message.reply_text("Invalid selection. Please choose a valid number.")
        elif text.lower() == "search again":
            user_states[user_id]["state"] = "expecting_job_title"
            save_user_states()
            await update.message.reply_text(
                "Please enter a new job title.",
                reply_markup=ReplyKeyboardRemove()
            )

    elif state == "expecting_job_selection":
        await update.message.reply_text(
            "Please use the numbered buttons (1-5) or 'More' to select a job.",
            reply_markup=ReplyKeyboardMarkup([['1', '2', '3', '4', '5', 'More']], resize_keyboard=True)
        )

    else:
        await update.message.reply_text(
            "❓ Unexpected input. Please send /start to begin again.",
            reply_markup=ReplyKeyboardRemove()
        )

async def generate_cv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_states.get(user_id, {}).get("state", "")
    active_job = user_states.get(user_id, {}).get("active_job")
    if not active_job:
        await update.message.reply_text("No job offer selected. Please insert or find a job first.")
        return
    # ToDo
    await update.message.reply_text("📝 Generating CV for your selected job...")
    cv_text = generate_cv(active_job, user_id)
    await update.message.reply_text(f"📄 Generated CV:\n\n{cv_text}")
    await update.message.reply_text("🔍 Evaluating CV quality...")
    evaluation = evaluate_cv_quality(cv_text)
    await update.message.reply_text(f"✅ CV Quality Evaluation:\n\n{evaluation}")

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
        "Please enter the job title you're interested in.",
        reply_markup=ReplyKeyboardRemove()
    )

async def handle_job_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    jobs = user_states[user_id].get("job_search_results", [])
    index = user_states[user_id].get("job_search_index", 0)

    if text.isdigit() and 1 <= int(text) <= 5:
        job_idx = index + int(text) - 1
        if job_idx < len(jobs):
            selected_job = jobs[job_idx]
            user_states[user_id]["active_job"] = selected_job["description"]
            user_states[user_id]["state"] = "ready"
            save_user_states()
            await update.message.reply_text(
                f"✅ Selected job: {selected_job['title']}\n\nYou can now generate a tailored CV.",
                reply_markup=main_keyboard
            )
        else:
            await update.message.reply_text("Invalid selection.")
    elif text == "More":
        next_index = index + 5
        if next_index < len(jobs):
            user_states[user_id]["job_search_index"] = next_index
            save_user_states()
            await send_job_selection(update, jobs, next_index)
        else:
            await update.message.reply_text("No more jobs to show.")
    else:
        await update.message.reply_text(
            "Please use the numbered buttons (1-5) or 'More' to select a job.",
            reply_markup=ReplyKeyboardMarkup([['1', '2', '3', '4', '5', 'More']], resize_keyboard=True)
        )

async def send_job_selection(update: Update, jobs, start_index):
    keyboard = []
    job_msgs = []
    for i in range(start_index, min(start_index + 5, len(jobs))):
        job = jobs[i]
        job_msgs.append(f"{i - start_index + 1}. {job['title']}\n{job.get('company', '')}\n{job['description'][:150]}...")
    keyboard = [['1', '2', '3', '4', '5', 'More']]
    await update.message.reply_text(
        "Top jobs:\n\n" + "\n\n".join(job_msgs),
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def send_job_offers(update, jobs):
    for idx, job in enumerate(jobs, 1):
        # Customize this formatting as needed
        text = f"{idx}. {job['title']}\n{job.get('company', '')}\n{job['description'][:200]}..."
        await update.message.reply_text(text)
    keyboard = [['1', '2', '3', '4', '5'], ['Search again']]
    await update.message.reply_text(
        "Reply with the number (1-5) of the job you want to pick, or tap 'Search again' to enter a new job title.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


async def generate_cv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cv_text = "Your CV content here"  # Replace with actual CV text retrieval logic

    base_dir = os.path.dirname(os.path.dirname(__file__))
    wkhtmltopdf_path = os.path.join(base_dir, "wkhtmltopdf", "bin", "wkhtmltopdf.exe")
    md_path = f"cv_{user_id}.md"
    pdf_path = f"cv_{user_id}.pdf"

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
