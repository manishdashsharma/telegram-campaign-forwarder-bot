import json
import os
import uuid
import logging
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackContext
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

campaign_file = 'campaigns.json'
chat_log_file = 'chat_ids.json'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Functions to load and save campaigns and chat IDs
def load_campaigns():
    try:
        with open(campaign_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error reading campaigns file: {e}")
        return {}

def load_chat_ids():
    try:
        with open(chat_log_file, 'r') as f:
            chats = json.load(f)
            return [str(chat['chat_id']) for chat in chats]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error reading chat IDs file: {e}")
        return []

def save_campaigns(data):
    try:
        with open(campaign_file, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving campaigns: {e}")

# Class to handle campaign forwarding
class TelegramForwarder:
    def __init__(self, bot_token, skip_groups):
        self.bot = Bot(bot_token)
        self.skip_groups = skip_groups
        self.running_campaigns = {}

    def parse_duration(self, duration_str):
        if duration_str.endswith('min'):
            return int(duration_str.rstrip('min')) * 60
        return 60  # default 1 minute

    async def forward_campaign(self, campaign_link, group_ids):
        """Forwards the campaign link to all specified groups."""
        for group_id in group_ids:
            if group_id not in self.skip_groups:
                try:
                    await self.bot.send_message(group_id, campaign_link)
                    logger.info(f"Successfully sent to group {group_id}")
                except Exception as e:
                    logger.error(f"Failed to send to group {group_id}: {e}")

    async def schedule_campaign(self, campaign_id, campaign_link, duration_str):
        """Schedules the campaign and forwards it periodically."""
        seconds = self.parse_duration(duration_str)
        self.running_campaigns[campaign_id] = True
        group_ids = load_chat_ids()

        while self.running_campaigns.get(campaign_id, False):
            await self.forward_campaign(campaign_link, group_ids)
            await asyncio.sleep(seconds)  # Wait before next forwarding

            # Check if the campaign is still marked as active
            campaigns = load_campaigns()
            if not campaigns.get(campaign_id, {}).get("active", False):
                logger.info(f"Stopping campaign {campaign_id} as it's marked inactive")
                break

        self.running_campaigns.pop(campaign_id, None)

    def stop_scheduled_campaign(self, campaign_id):
        """Stops a running campaign."""
        if campaign_id in self.running_campaigns:
            self.running_campaigns[campaign_id] = False

# Command handlers
async def create_campaign(update: Update, context: CallbackContext):
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /create_campaign {ads_link} {duration_in_minutes}min")
        return

    ads_link = context.args[0]
    duration = context.args[1]
    if not duration.endswith('min'):
        duration += 'min'
    
    campaigns = load_campaigns()
    campaign_id = str(uuid.uuid4())
    campaigns[campaign_id] = {
        "ads_link": ads_link,
        "duration": duration,
        "active": True,
        "created_at": datetime.now().isoformat()
    }

    save_campaigns(campaigns)
    await update.message.reply_text(f"Campaign created with ID: {campaign_id}\nLink: {ads_link}\nDuration: {duration}")

async def update_campaign(update: Update, context: CallbackContext):
    if len(context.args) != 3:
        await update.message.reply_text("Usage: /update_campaign {id} {ads_link} {duration_in_minutes}min")
        return

    campaign_id, ads_link, duration = context.args
    if not duration.endswith('min'):
        duration += 'min'
    
    campaigns = load_campaigns()

    if campaign_id not in campaigns:
        await update.message.reply_text(f"No campaign found with ID: {campaign_id}")
        return

    campaigns[campaign_id].update({
        "ads_link": ads_link,
        "duration": duration,
        "updated_at": datetime.now().isoformat()
    })
    
    save_campaigns(campaigns)
    await update.message.reply_text(f"Campaign {campaign_id} updated:\nLink: {ads_link}\nDuration: {duration}")

async def delete_campaign(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /delete_campaign {id}")
        return

    campaign_id = context.args[0]
    campaigns = load_campaigns()

    if campaign_id not in campaigns:
        await update.message.reply_text(f"No campaign found with ID: {campaign_id}")
        return

    del campaigns[campaign_id]
    save_campaigns(campaigns)
    await update.message.reply_text(f"Campaign {campaign_id} deleted.")

async def start_campaign(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /start_campaign {id}")
        return

    campaign_id = context.args[0]
    campaigns = load_campaigns()

    if campaign_id not in campaigns:
        await update.message.reply_text(f"No campaign found with ID: {campaign_id}")
        return

    if not campaigns[campaign_id]["active"]:
        await update.message.reply_text(f"Campaign {campaign_id} is not active.")
        return

    try:
        await update.message.reply_text(f"Starting campaign {campaign_id} forwarding...")

        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise ValueError("BOT_TOKEN not found in environment variables")

        skip_groups = os.getenv("SKIP_GROUP", "").strip("[]").split(",")
        skip_groups = [group.strip() for group in skip_groups]

        forwarder = TelegramForwarder(bot_token, skip_groups)
        asyncio.create_task(forwarder.schedule_campaign(
            campaign_id,
            campaigns[campaign_id]["ads_link"],
            campaigns[campaign_id]["duration"]
        ))

        campaigns[campaign_id]["last_run"] = datetime.now().isoformat()
        save_campaigns(campaigns)
        
        await update.message.reply_text(f"Campaign {campaign_id} scheduled and started.")
    
    except Exception as e:
        logger.error(f"Error in start_campaign: {e}")
        await update.message.reply_text(f"An error occurred: {str(e)}")

async def stop_campaign(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /stop_campaign {id}")
        return

    campaign_id = context.args[0]
    campaigns = load_campaigns()

    if campaign_id not in campaigns:
        await update.message.reply_text(f"No campaign found with ID: {campaign_id}")
        return

    bot_token = os.getenv("BOT_TOKEN")
    skip_groups = os.getenv("SKIP_GROUP", "").strip("[]").split(",")
    forwarder = TelegramForwarder(bot_token, skip_groups)
    forwarder.stop_scheduled_campaign(campaign_id)

    campaigns[campaign_id].update({
        "active": False,
        "stopped_at": datetime.now().isoformat()
    })
    save_campaigns(campaigns)
    await update.message.reply_text(f"Campaign {campaign_id} stopped and marked as inactive.")

async def list_campaigns(update: Update, context: CallbackContext):
    campaigns = load_campaigns()

    if not campaigns:
        await update.message.reply_text("No campaigns available.")
        return

    message = "List of Campaigns:\n\n"
    for campaign_id, details in campaigns.items():
        status = "Active" if details.get("active", False) else "Inactive"
        message += (f"ID: {campaign_id}\n"
                   f"Link: {details['ads_link']}\n"
                   f"Duration: {details['duration']}\n"
                   f"Status: {status}\n"
                   f"Created: {details.get('created_at', 'N/A')}\n\n")

    await update.message.reply_text(message)

async def error_handler(update: Update, context: CallbackContext):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    try:
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise ValueError("BOT_TOKEN not found in environment variables")

        app = Application.builder().token(bot_token).build()

        app.add_handler(CommandHandler("create_campaign", create_campaign))
        app.add_handler(CommandHandler("update_campaign", update_campaign))
        app.add_handler(CommandHandler("delete_campaign", delete_campaign))
        app.add_handler(CommandHandler("start_campaign", start_campaign))
        app.add_handler(CommandHandler("stop_campaign", stop_campaign))
        app.add_handler(CommandHandler("list_campaigns", list_campaigns))
        app.add_error_handler(error_handler)

        logger.info("Bot started successfully")
        app.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    main()
