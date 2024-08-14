from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import aiohttp
from dotenv import load_dotenv

load_dotenv()

HADITH_API_KEY = os.getenv("HADITH_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

HADITH_API_URL = HADITH_API_KEY

hadith_data = {
    '1': ['Hadith 1.1', 'Hadith 1.2'],
    '2': ['Hadith 2.1', 'Hadith 2.2'],
}


user_preferences = {}

async def fetch_hadith(language):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{HADITH_API_URL}") as response:
                data = await response.json()
                hadiths = data.get('hadiths', [])
                filtered_hadiths = [
                    hadith[f'hadith{language.capitalize()}'] for hadith in hadiths
                ]
                return filtered_hadiths
    except Exception as e:
        print(f"Error fetching hadiths: {e}")
        return []

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if not context.args:
        await update.message.reply_text("Please specify the language (Arabic or English).")
        return

    language = context.args[0].lower()
    if language not in ['arabic', 'english']:
        await update.message.reply_text("Invalid language. Please choose 'Arabic' or 'English'.")
        return

    user_preferences[user_id] = language
    await update.message.reply_text(f"Language set to {language.capitalize()}.")

MAX_MESSAGE_LENGTH = 4096

async def set_chapter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if not context.args:
        await update.message.reply_text("Please specify the chapter number.")
        return

    chapter = context.args[0]
    if chapter not in hadith_data:
        await update.message.reply_text("Invalid chapter. Please choose a valid chapter number.")
        return

    user_preferences[user_id] = chapter
    hadiths = hadith_data[chapter]
    hadith_text = "\n".join(hadiths)

    if len(hadith_text) > MAX_MESSAGE_LENGTH:
        for i in range(0, len(hadith_text), MAX_MESSAGE_LENGTH):
            chunk = hadith_text[i:i + MAX_MESSAGE_LENGTH]
            await update.message.reply_text(chunk)
    else:
        await update.message.reply_text(f"Chapter set to {chapter}. Here are the hadiths:\n{hadith_text}")

async def get_hadith(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    language = user_preferences.get(user_id, 'arabic')
    hadiths = await fetch_hadith(language)

    if hadiths:
        combined_hadiths = "\n\n".join(hadiths)
        if len(combined_hadiths) > MAX_MESSAGE_LENGTH:
            for i in range(0, len(combined_hadiths), MAX_MESSAGE_LENGTH):
                chunk = combined_hadiths[i:i + MAX_MESSAGE_LENGTH]
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(combined_hadiths)
    else:
        await update.message.reply_text("No Hadith found.")

async def list_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    commands = (
        "/hello - Responds with a greeting message.\n"
        "/setlanguage <language> - Sets the language preference (Arabic or English).\n"
        "/hadith - Retrieves all Hadiths in the selected language.\n"
        "/set_chapter <chapter number> - Sets the chapter number\n"
        "/commands - Lists all available commands."
    )
    await update.message.reply_text(commands)

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello there!")

def main() -> None:
    token = TELEGRAM_BOT_TOKEN
    application = Application.builder().token(token).concurrent_updates(True).read_timeout(30).write_timeout(30).build()
    application.add_handler(CommandHandler("hello", reply))
    application.add_handler(CommandHandler("setlanguage", set_language))
    application.add_handler(CommandHandler("hadith", get_hadith))
    application.add_handler(CommandHandler('set_chapter', set_chapter))
    application.add_handler(CommandHandler("commands", list_commands))
    application.add_handler(MessageHandler(filters.TEXT, reply))
    application.add_handler(MessageHandler(filters.PHOTO, reply))
    print("Telegram Bot started!", flush=True)
    application.run_polling()

if __name__ == '__main__':
    main()
