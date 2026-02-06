from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from rembg import remove
from PIL import Image
import os

TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_PATH = "/webhook"

app = FastAPI()
application = ApplicationBuilder().token(TOKEN).build()


# ===== handlers =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً! أرسل صورة وأنا أزيل الخلفية."
    )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أرسل صورة (Photo أو Document) وسيتم إزالة الخلفية."
    )

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    os.makedirs("temp", exist_ok=True)

    if update.message.photo:
        file = update.message.photo[-1]
        filename = f"{file.file_unique_id}.jpg"

    elif update.message.document and update.message.document.mime_type.startswith("image/"):
        file = update.message.document
        ext = os.path.splitext(file.file_name)[1]
        filename = f"{file.file_unique_id}{ext}"
    else:
        return

    input_path = f"temp/{filename}"
    tg_file = await context.bot.get_file(file.file_id)
    await tg_file.download_to_drive(input_path)

    await update.message.reply_text("⏳ عم نعالج الصورة...")

    output_path = process_image(input_path)

    await update.message.reply_document(open(output_path, "rb"))

    os.remove(input_path)
    os.remove(output_path)


def process_image(input_path: str):
    name, _ = os.path.splitext(input_path)
    output_path = f"{name}_white.png"

    img = Image.open(input_path)
    removed = remove(img).convert("RGBA")

    white_bg = Image.new("RGBA", removed.size, (255, 255, 255, 255))
    final = Image.alpha_composite(white_bg, removed).convert("RGB")

    final.save(output_path, "PNG")
    return output_path


# ===== webhook =====

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}


@app.on_event("startup")
async def on_startup():
    await application.initialize()

    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    webhook_url = f"{render_url}{WEBHOOK_PATH}"

    await application.bot.set_webhook(webhook_url)


@app.on_event("shutdown")
async def on_shutdown():
    await application.shutdown()


# ===== register handlers =====

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help))
application.add_handler(
    MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_image)
)
