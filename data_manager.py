import json
import os
import logging
from config import DATA_FILE

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def load_data():
    """Load tracked products data from JSON file."""
    if not os.path.exists(DATA_FILE):
        return {}
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Error parsing {DATA_FILE}. File might be corrupted.")
        return {}
    except Exception as e:
        logger.error(f"Error loading data from {DATA_FILE}: {e}")
        return {}

def save_data(data):
    """Save tracked products data to JSON file."""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving data to {DATA_FILE}: {e}")
        return False

def add_product(chat_id, product_url, product_name, price):
    """Add a product to tracked products."""
    data = load_data()
    
    # Create chat_id entry if it doesn't exist
    if str(chat_id) not in data:
        data[str(chat_id)] = {}
    
    # Add or update the product
    data[str(chat_id)][product_url] = {
        "initial_price": price,
        "current_price": price,
        "product_name": product_name
    }
    
    return save_data(data)

def remove_product(chat_id, product_url):
    """Remove a product from tracked products."""
    data = load_data()
    
    # Check if chat_id exists
    if str(chat_id) not in data:
        return False
    
    # Check if product_url exists in chat_id
    if product_url not in data[str(chat_id)]:
        return False
    
    # Remove the product
    del data[str(chat_id)][product_url]
    
    # Remove the chat_id if there are no products left
    if not data[str(chat_id)]:
        del data[str(chat_id)]
    
    return save_data(data)

def get_all_products(chat_id=None):
    """Get all tracked products, optionally filtered by chat_id."""
    data = load_data()
    
    if chat_id is not None:
        return data.get(str(chat_id), {})
    
    return data

def update_product_price(chat_id, product_url, new_price):
    """Update current price of a product."""
    data = load_data()
    
    # Check if chat_id and product_url exist
    if str(chat_id) not in data or product_url not in data[str(chat_id)]:
        return False
    
    # Update the current price
    data[str(chat_id)][product_url]["current_price"] = new_price
    
    return save_data(data)

def get_threshold(chat_id):
    """Get the price change threshold for a specific chat. Returns default if not set."""
    from config import PRICE_CHANGE_THRESHOLD
    data = load_data()
    
    if str(chat_id) not in data:
        return PRICE_CHANGE_THRESHOLD
    
    # Get threshold from chat settings, or use default if not set
    return data[str(chat_id)].get('_threshold', PRICE_CHANGE_THRESHOLD)

def set_threshold(chat_id, threshold):
    """Set the price change threshold for a specific chat."""
    data = load_data()
    
    # Create chat_id entry if it doesn't exist
    if str(chat_id) not in data:
        data[str(chat_id)] = {}
    
    # Store threshold in a special key (prefixed with _ to distinguish from product URLs)
    data[str(chat_id)]['_threshold'] = float(threshold)
    
    return save_data(data)
