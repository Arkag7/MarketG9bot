import os
import logging
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from google import genai

logging.basicConfig(level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

# Initialize Gemini client
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI()
ptb_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🚀 *MarketG9 Market Intelligence Bot*\n\n"
        "Send `/analyze <industry or company>` to generate strategic market briefs covering:\n"
        "• Industry Trends & Macro Drivers\n"
        "• Distribution Channels & Territory Conflicts\n"
        "• Key Risks & Strategic Opportunities"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("⚠️ Usage: `/analyze <target industry, company, or market>`", parse_mode="Markdown")
        return

    status_msg = await update.message.reply_text("🔍 *Scanning market signals and industry data...*", parse_mode="Markdown")

    prompt = f"""
    You are a B2B Market Intelligence analyst. Conduct a structured assessment for: {query}.
    
    Provide:
    1. **Industry Trends & Macro Drivers**
    2. **Distribution Channels & Territory Conflicts**
    3. **Key Risks & Emerging Opportunities**
    4. **Actionable Recommendations**
    
    Keep output structured, concise, and formatted in clean Markdown.
    """

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
            text=response.text,
            parse_mode="Markdown"
        )
    except Exception as e:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
            text=f"❌ Error generating intelligence report: {str(e)}"
        )

ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(CommandHandler("analyze", analyze))

@app.on_event("startup")
async def startup():
    await ptb_app.initialize()
    await ptb_app.start()
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/telegram"
        await ptb_app.bot.set_webhook(url=webhook_url)

@app.post("/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, ptb_app.bot)
    await ptb_app.process_update(update)
    return Response(status_code=200)

@app.get("/")
async def health():
    return {"status": "ok", "service": "MarketG9 Bot"}
