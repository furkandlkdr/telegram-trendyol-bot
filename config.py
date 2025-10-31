import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Telegram bot token
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Check interval in minutes
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '30'))

# Allowed Group IDs
ALLOWED_GROUP_IDS_STR = os.getenv('ALLOWED_GROUP_IDS', '')
ALLOWED_GROUP_IDS = [int(group_id.strip()) for group_id in ALLOWED_GROUP_IDS_STR.split(',') if group_id.strip()]

# Admin Chat ID for error notifications
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID', '')

if not ALLOWED_GROUP_IDS:
    logger.warning("No ALLOWED_GROUP_IDS set in .env file. Bot will not respond to any group.")

if not ADMIN_CHAT_ID:
    logger.warning("No ADMIN_CHAT_ID set in .env file. Error notifications will not be sent.")

# File to store tracked product data
DATA_FILE = 'tracked_products.json'

# User agent for requests
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Price change notification threshold (in percentage)
PRICE_CHANGE_THRESHOLD = 5.0  # Only notify if price changes by more than 5%

