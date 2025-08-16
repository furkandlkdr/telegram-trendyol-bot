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

# Discord bot token
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Check interval in minutes
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '30'))

# Admin User ID for error notifications
ADMIN_USER_ID = os.getenv('ADMIN_USER_ID', '')

if not ADMIN_USER_ID:
    logger.warning("No ADMIN_USER_ID set in .env file. Error notifications will not be sent.")

# File to store tracked product data
DATA_FILE = 'tracked_products.json'

# User agent for requests
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
