import os
import json
import logging
from telegram import Update, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, ChatMemberHandler, CallbackContext, filters
from dotenv import load_dotenv

load_dotenv()

CHAT_LOG_FILE = os.path.join(os.getcwd(), "chat_ids.json")
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def load_chat_data():
    try:
        if os.path.exists(CHAT_LOG_FILE):
            with open(CHAT_LOG_FILE, "r") as file:
                return json.load(file)
    except json.JSONDecodeError as e:
        logger.error(f"Error reading JSON file: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading chat data: {e}")
        return []
    return []

def save_chat_data(chat_data):
    try:
        with open(CHAT_LOG_FILE, "w") as file:
            json.dump(chat_data, file, indent=4)
        logger.info(f"Successfully saved chat data for {len(chat_data)} chats")
    except Exception as e:
        logger.error(f"Error saving chat data: {e}")

async def handle_bot_added(update: Update, context: CallbackContext):
    """Handles when the bot is added to a group or channel."""
    try:
        chat = update.my_chat_member.chat
        chat_id = str(chat.id)
        chat_type = chat.type
        chat_name = chat.title or "Private Chat"

        chat_entry = {
            "name": chat_name, 
            "chat_id": chat_id, 
            "type": chat_type,
            "added_at": update.my_chat_member.date.isoformat()
        }
        
        chat_data = load_chat_data()
        
        if not any(str(entry["chat_id"]) == chat_id for entry in chat_data):
            chat_data.append(chat_entry)
            save_chat_data(chat_data)
            logger.info(f"Added new chat: {chat_name} ({chat_id})")
        
    except Exception as e:
        logger.error(f"Error handling bot addition: {e}")

async def error_handler(update: Update, context: CallbackContext):
    """Log any errors that occur during bot operation."""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    try:
        if not os.getenv("BOT_TOKEN"):
            raise ValueError("BOT_TOKEN not found in environment variables")
            
        app = Application.builder().token(os.getenv("BOT_TOKEN")).build()
        app.add_handler(ChatMemberHandler(handle_bot_added, ChatMemberHandler.MY_CHAT_MEMBER))
        app.add_error_handler(error_handler)
        
        logger.info("Bot started successfully")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    main()