import telebot
import threading
import time
import os
from telebot import types
from report_generator import ReportGenerator

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from docx import Document

BOT_TOKEN = "8455804390:AAHvaU0MRRVPAyJHnxR4yqZnZ9X3G1ASxLo"

bot = telebot.TeleBot(BOT_TOKEN)
generator = ReportGenerator()

# ---------------- SESSION MEMORY ----------------
users = {}  # chat_id -> dict


def get_user(chat_id):
    if chat_id not in users:
        users[chat_id] = {}
    return users[chat_id]


# ---------------- FILE GENERATORS ----------------
def create_pdf(report_text, filename):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(filename, pagesize=A4)
    story = []

    for line in report_text.split("\n"):
        story.append(Paragraph(line.replace("&", "&amp;"), styles["Normal"]))

    doc.build(story)


def create_docx(report_text, filename):
    doc = Document()
    for line in report_text.split("\n"):
        doc.add_paragraph(line)
    doc.save(filename)


# ---------------- ANIMATION ----------------
def typing(chat_id, stop_event):
    while not stop_event.is_set():
        bot.send_chat_action(chat_id, "typing")
        time.sleep(4)


def generate_report_async(chat_id):
    user = get_user(chat_id)
    stop_event = threading.Event()
    threading.Thread(target=typing, args=(chat_id, stop_event)).start()

    try:
        report = generator.generate_report(
            data_content=user["content"],
            data_type=user["data_type"],
            user_name=user.get("name", "User"),
            user_role=user.get("job", "Owner"),
            business_type=user.get("business", "General Business"),
            report_focus=user.get("report_focus", "full")
        )

        stop_event.set()

        # -------- TEXT OUTPUT (UNCHANGED) --------
        for i in range(0, len(report), 4000):
            bot.send_message(chat_id, report[i:i + 4000])

        # -------- FILE OUTPUT --------
        base = f"Business_Report_{chat_id}"
        pdf_file = f"{base}.pdf"
        docx_file = f"{base}.docx"

        create_pdf(report, pdf_file)
        create_docx(report, docx_file)

        bot.send_document(chat_id, open(pdf_file, "rb"))
        bot.send_document(chat_id, open(docx_file, "rb"))

        os.remove(pdf_file)
        os.remove(docx_file)

    except Exception as e:
        stop_event.set()
        bot.send_message(chat_id, f"❌ Error: {e}")


# ---------------- CHAT FLOW ----------------
@bot.message_handler(commands=["start"])
def start(message):
    get_user(message.chat.id).clear()
    bot.reply_to(
        message,
        "👋 Hi! I’m your *AI Business Companion*.\n\nWhat’s your *name*?",
        parse_mode="Markdown"
    )


@bot.message_handler(func=lambda m: "name" not in get_user(m.chat.id))
def get_name(message):
    get_user(message.chat.id)["name"] = message.text
    bot.reply_to(message, "Nice to meet you! What’s your *job role*?")


@bot.message_handler(func=lambda m: "job" not in get_user(m.chat.id))
def get_job(message):
    get_user(message.chat.id)["job"] = message.text
    bot.reply_to(message, "What type of *business* is this?")


@bot.message_handler(func=lambda m: "business" not in get_user(m.chat.id))
def get_business(message):
    get_user(message.chat.id)["business"] = message.text
    bot.reply_to(message, "Now send your data (Text / CSV / JSON / Excel)")


# ---------------- DATA INPUT ----------------
@bot.message_handler(content_types=["text"])
def receive_text(message):
    user = get_user(message.chat.id)
    if "content" not in user:
        user["content"] = message.text
        user["data_type"] = "text"
        ask_report_type(message.chat.id)


@bot.message_handler(content_types=["document"])
def receive_file(message):
    user = get_user(message.chat.id)

    file_bytes = bot.download_file(
        bot.get_file(message.document.file_id).file_path
    )
    filename = message.document.file_name.lower()

    if filename.endswith(".csv"):
        user["data_type"] = "csv"
        user["content"] = file_bytes.decode("utf-8", errors="ignore")
    elif filename.endswith(".json"):
        user["data_type"] = "json"
        user["content"] = file_bytes.decode("utf-8", errors="ignore")
    elif filename.endswith(".xlsx"):
        user["data_type"] = "excel"
        user["content"] = file_bytes
    else:
        bot.send_message(message.chat.id, "❌ Unsupported file type")
        return

    ask_report_type(message.chat.id)


# ---------------- REPORT TYPE ----------------
def ask_report_type(chat_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("📈 Profit Analysis", callback_data="profit"),
        types.InlineKeyboardButton("📉 Loss Analysis", callback_data="loss"),
        types.InlineKeyboardButton("📊 Full Review", callback_data="full")
    )
    bot.send_message(chat_id, "What report do you want?", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data in ["profit", "loss", "full"])
def choose_report(call):
    get_user(call.message.chat.id)["report_focus"] = call.data
    bot.send_message(call.message.chat.id, "🧠 Generating report…")

    threading.Thread(
        target=generate_report_async,
        args=(call.message.chat.id,)
    ).start()


# ---------------- RUN ----------------
if __name__ == "__main__":
    print("🤖 Telegram bot running (PDF + Word enabled)")
    bot.infinity_polling(skip_pending=True)
