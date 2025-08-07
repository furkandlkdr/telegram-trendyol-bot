import requests
from bs4 import BeautifulSoup
import re
from config import USER_AGENT
import logging
import json
import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Request configuration
MAX_RETRIES = 3
BACKOFF_FACTOR = 2
TIMEOUT = 15
MIN_DELAY = 1
MAX_DELAY = 3

def create_session():
    """Create a robust HTTP session with retry strategy."""
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=MAX_RETRIES,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=BACKOFF_FACTOR,
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def add_random_delay():
    """Add random delay between requests to avoid rate limiting."""
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    time.sleep(delay)
    logger.debug(f"Added {delay:.2f}s delay")

def is_valid_trendyol_url(url):
    """Check if the URL is a valid Trendyol URL."""
    return bool(re.match(r'https?://(www\.)?(trendyol\.com|ty\.gl|tyml\.gl|trendyol-milla\.com).*', url))

def get_full_url(url):
    """Follow redirects to get the full URL if it's a shortened link."""
    try:
        add_random_delay()
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        session = create_session()
        response = session.head(url, headers=headers, allow_redirects=True, timeout=TIMEOUT)
        return response.url
    except requests.exceptions.Timeout:
        logger.error(f"Timeout following redirect for {url}")
        return url
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error following redirect for {url}: {e}")
        return url
    except Exception as e:
        logger.error(f"Error following redirect for {url}: {e}")
        return url

def extract_price(text):
    """Extract numeric price value from text."""
    if not text:
        return None
    # Remove spaces and replace comma with dot
    price_text = text.strip().replace('.', '').replace(',', '.')
    # Extract numbers with decimal points using regex
    match = re.search(r'(\d+[,.]\d+|\d+)', price_text)
    if match:
        price = float(match.group(1).replace(',', '.'))
        # Add reasonable bounds check to avoid interpreting IDs as prices
        if 0.01 <= price <= 100000:  # Reasonable price range
            return price
    return None

def scrape_product_info(url):
    """Scrape product information from Trendyol with improved error handling."""
    last_error = None
    
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Scraping attempt {attempt + 1}/{MAX_RETRIES} for {url}")
            
            # Follow redirects for shortened URLs
            full_url = get_full_url(url)
            
            # Check if the URL is a valid Trendyol URL
            if not is_valid_trendyol_url(full_url):
                return None, None, "URL does not belong to Trendyol"
            
            # Add delay before making request
            if attempt > 0:
                delay = BACKOFF_FACTOR ** attempt + random.uniform(1, 3)
                logger.info(f"Waiting {delay:.2f}s before retry...")
                time.sleep(delay)
            else:
                add_random_delay()
            
            headers = {
                'User-Agent': USER_AGENT,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            
            session = create_session()
            response = session.get(full_url, headers=headers, timeout=TIMEOUT)
            
            if response.status_code != 200:
                last_error = f"HTTP {response.status_code}"
                logger.warning(f"HTTP {response.status_code} for {url}, attempt {attempt + 1}")
                if attempt == MAX_RETRIES - 1:
                    return None, None, f"Failed to access product page. Status code: {response.status_code}"
                continue
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # **Product name extraction - Updated structure**
            product_name = None
            
            # Method 1: New Trendyol structure - h1 with data-testid
            h1_tag = soup.find('h1', attrs={'data-testid': 'product-name'})
            if h1_tag:
                product_name = h1_tag.text.strip()
            
            # Method 2: General h1 search
            elif soup.find('h1'):
                product_name = soup.find('h1').text.strip()
            
            # Method 3: Extract from title (fallback)
            elif soup.find('title'):
                title_text = soup.find('title').text
                product_name = title_text.split('-')[0].strip() if title_text else None
            
            # **Stock check - Updated structure**
            is_sold_out = False
            stock_confirmed = False  # Flag for positive stock confirmation
            
            # Method 1: Add to cart button check (MOST IMPORTANT)
            add_to_cart_btn = soup.find('button', attrs={'data-testid': 'add-to-cart-button'})
            if add_to_cart_btn:
                btn_text = add_to_cart_btn.get_text().strip()
                # If button says "Add to Cart" it means in stock
                if 'Sepete Ekle' in btn_text:
                    is_sold_out = False
                    stock_confirmed = True
                    logger.info(f"Product is in stock - add to cart button found")
                elif 'Tükendi' in btn_text or 'Stok Yok' in btn_text or 'Mevcut Değil' in btn_text:
                    is_sold_out = True
                    stock_confirmed = True
                    logger.info(f"Product is sold out - button indicates no stock")
            
            # Method 2: Buy now button check (reinforcing)
            if not stock_confirmed:
                buy_now_btn = soup.find('button', class_='buy-now-button')
                if buy_now_btn:
                    btn_text = buy_now_btn.get_text().strip()
                    if 'Şimdi Al' in btn_text:
                        is_sold_out = False
                        stock_confirmed = True
                        logger.info(f"Product is in stock - buy now button found")
            
            # Method 3: Disabled button check (only if positive control is missing)
            if not stock_confirmed:
                disabled_buttons = soup.find_all('button', disabled=True)
                for btn in disabled_buttons:
                    btn_classes = btn.get('class', [])
                    if any('add-to-cart' in str(cls) or 'sepete-ekle' in str(cls) for cls in btn_classes):
                        is_sold_out = True
                        stock_confirmed = True
                        logger.info("Product is sold out - add to cart button is disabled")
                        break
            
            # Method 4: General out of stock messages (only if positive control is missing)
            if not stock_confirmed:
                # Only search in visible text elements, ignore JavaScript content
                visible_elements = soup.find_all(['div', 'span', 'p', 'h1', 'h2', 'h3', 'button'], 
                                               class_=lambda x: x and 'stock' in ' '.join(x).lower() if x else False)
                
                for element in visible_elements:
                    text = element.get_text().strip().lower()
                    if any(phrase in text for phrase in ['tükendi', 'stok yok', 'mevcut değil', 'satışta değil']):
                        # But not if it's JavaScript or metadata
                        if len(text) < 100 and not any(js_indicator in text for js_indicator in ['window', 'function', 'var ', '__']):
                            is_sold_out = True
                            stock_confirmed = True
                            logger.info(f"Sold out detected via visible text: {text}")
                            break
            
            if is_sold_out:
                logger.info(f"Product is sold out: {product_name}")
                return product_name, 0, "Tükendi"
            
            # **Price extraction - Updated structure**
            price = None
            
            # Method 1: New - data-testid price search
            price_container = soup.find('div', attrs={'data-testid': 'price'})
            if price_container:
                logger.debug(f"Found price container: {price_container}")
                
                # Get discounted price if available
                discounted_price = price_container.find('span', class_='price-view-discounted')
                if discounted_price:
                    price = extract_price(discounted_price.text)
                    logger.info(f"Found discounted price: {price}")
                
                # Get original price if no discount
                if not price:
                    original_price = price_container.find('span', class_='price-view-original')
                    if original_price:
                        price = extract_price(original_price.text)
                        logger.info(f"Found original price: {price}")
                
                # Any span with price-view class
                if not price:
                    price_view_spans = price_container.find_all('span', class_=lambda x: x and 'price-view' in ' '.join(x))
                    for span in price_view_spans:
                        text = span.get_text()
                        if 'TL' in text or '₺' in text:
                            extracted_price = extract_price(text)
                            if extracted_price:
                                price = extracted_price
                                logger.info(f"Found price in price-view span: {price}")
                                break
                
                # Any price element
                if not price:
                    price_spans = price_container.find_all('span')
                    for span in price_spans:
                        text = span.get_text()
                        if 'TL' in text or '₺' in text:
                            extracted_price = extract_price(text)
                            if extracted_price:
                                price = extracted_price
                                logger.info(f"Found price in span: {price}")
                                break
            
            # Method 2: price-price class price search (new structure)
            if not price:
                price_price_divs = soup.find_all('div', class_=lambda x: x and 'price-price' in ' '.join(x))
                for div in price_price_divs:
                    spans = div.find_all('span')
                    for span in spans:
                        text = span.get_text()
                        if 'TL' in text or '₺' in text:
                            extracted_price = extract_price(text)
                            if extracted_price:
                                price = extracted_price
                                logger.info(f"Found price via price-price class: {price}")
                                break
                    if price:
                        break
            
            # Method 3: Old structure - campaign-price
            if not price:
                price_tag = soup.find('p', class_='campaign-price')
                if price_tag:
                    price = extract_price(price_tag.text)
                    logger.info(f"Found price via campaign-price: {price}")
            
            # Method 4: Old structure - prc-dsc
            if not price:
                price_tag = soup.find('span', class_='prc-dsc')
                if price_tag:
                    price = extract_price(price_tag.text)
                    logger.info(f"Found price via prc-dsc: {price}")
            
            # Method 5: JSON-LD structured data
            if not price:
                script_tags = soup.find_all('script', type='application/ld+json')
                for script in script_tags:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and 'offers' in data:
                            offers = data['offers']
                            if isinstance(offers, dict) and 'price' in offers:
                                price = float(offers['price'])
                                logger.info(f"Found price via JSON-LD: {price}")
                                break
                            elif isinstance(offers, list) and offers:
                                if 'price' in offers[0]:
                                    price = float(offers[0]['price'])
                                    logger.info(f"Found price via JSON-LD array: {price}")
                                    break
                    except Exception:
                        continue
            
            # Method 6: JavaScript variables (winnerVariant)
            if not price:
                script_tags = soup.find_all('script')
                for script in script_tags:
                    if script.string and ('winnerVariant' in script.string or 'productDetail' in script.string):
                        # Extract price from JavaScript data
                        price_patterns = [
                            r'"price":\s*{\s*[^}]*"value":\s*([0-9.]+)',
                            r'"price":\s*([0-9.]+)',
                            r'"currentPrice":\s*([0-9.]+)',
                            r'"sellingPrice":\s*([0-9.]+)'
                        ]
                        
                        for pattern in price_patterns:
                            price_match = re.search(pattern, script.string)
                            if price_match:
                                price = float(price_match.group(1))
                                logger.info(f"Found price via JavaScript: {price}")
                                break
                        
                        if price:
                            break
            
            # Method 7: General TL/₺ search (last resort)
            if not price:
                price_elements = soup.find_all(string=re.compile(r'\d+[,.]?\d*\s*TL|\d+[,.]?\d*\s*₺'))
                for element in price_elements:
                    # Skip JavaScript content
                    parent = element.parent
                    if parent and parent.name == 'script':
                        continue
                        
                    extracted_price = extract_price(element)
                    if extracted_price and 1 <= extracted_price <= 100000:  # Reasonable price range
                        price = extracted_price
                        logger.info(f"Found price via general TL search: {price}")
                        break
            
            # Result validation
            if not product_name:
                return None, None, "Could not extract product name"
                
            if not price:
                logger.warning(f"Could not extract price for product: {product_name}")
                return product_name, None, "Could not extract price"
                
            logger.info(f"Successfully scraped - Product: {product_name}, Price: {price} TL")
            return product_name, price, None
        
        except requests.exceptions.Timeout as e:
            last_error = f"Timeout: {str(e)}"
            logger.warning(f"Timeout for {url}, attempt {attempt + 1}: {e}")
            
        except requests.exceptions.ConnectionError as e:
            last_error = f"Connection error: {str(e)}"
            logger.warning(f"Connection error for {url}, attempt {attempt + 1}: {e}")
            
        except requests.exceptions.RequestException as e:
            last_error = f"Request error: {str(e)}"
            logger.warning(f"Request error for {url}, attempt {attempt + 1}: {e}")
            
        except Exception as e:
            last_error = f"Unexpected error: {str(e)}"
            logger.warning(f"Unexpected error for {url}, attempt {attempt + 1}: {e}")
    
    # All attempts failed
    logger.error(f"All {MAX_RETRIES} attempts failed for {url}. Last error: {last_error}")
    return None, None, f"Failed after {MAX_RETRIES} attempts. Last error: {last_error}"
