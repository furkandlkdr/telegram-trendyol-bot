import aiohttp
from bs4 import BeautifulSoup
import re
from config import USER_AGENT
import logging
import json
import asyncio
import random

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

async def add_random_delay():
    """Add random delay between requests to avoid rate limiting."""
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    await asyncio.sleep(delay)
    logger.debug(f"Added {delay:.2f}s delay")

def is_valid_trendyol_url(url):
    """Check if the URL is a valid Trendyol URL."""
    return bool(re.match(r'https?://(www\.)?(trendyol\.com|ty\.gl|tyml\.gl|trendyol-milla\.com).*', url))

async def get_full_url(session, url):
    """Follow redirects to get the full URL if it's a shortened link."""
    try:
        await add_random_delay()
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        async with session.head(url, headers=headers, allow_redirects=True, timeout=TIMEOUT) as response:
            return str(response.url)
    except asyncio.TimeoutError:
        logger.error(f"Timeout following redirect for {url}")
        return url
    except aiohttp.ClientError as e:
        logger.error(f"Client error following redirect for {url}: {e}")
        return url
    except Exception as e:
        logger.error(f"Error following redirect for {url}: {e}")
        return url

def extract_price(text):
    """Extract numeric price value from text."""
    if not text:
        return None
    price_text = text.strip().replace('.', '').replace(',', '.')
    match = re.search(r'(\d+[,.]\d+|\d+)', price_text)
    if match:
        price = float(match.group(1).replace(',', '.'))
        if 0.01 <= price <= 100000:
            return price
    return None

async def scrape_product_info(url):
    """Scrape product information from Trendyol asynchronously."""
    last_error = None
    
    async with aiohttp.ClientSession() as session:
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Scraping attempt {attempt + 1}/{MAX_RETRIES} for {url}")
                
                full_url = await get_full_url(session, url)
                
                if not is_valid_trendyol_url(full_url):
                    return None, None, None, "URL does not belong to Trendyol"
                
                if attempt > 0:
                    delay = BACKOFF_FACTOR ** attempt + random.uniform(1, 3)
                    logger.info(f"Waiting {delay:.2f}s before retry...")
                    await asyncio.sleep(delay)
                else:
                    await add_random_delay()
                
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
                
                async with session.get(full_url, headers=headers, timeout=TIMEOUT) as response:
                    if response.status != 200:
                        last_error = f"HTTP {response.status}"
                        logger.warning(f"HTTP {response.status} for {url}, attempt {attempt + 1}")
                        if attempt == MAX_RETRIES - 1:
                            return None, None, None, f"Failed to access product page. Status code: {response.status}"
                        continue

                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')

                    product_name = None
                    h1_tag = soup.find('h1', attrs={'data-testid': 'product-name'})
                    if h1_tag:
                        product_name = h1_tag.text.strip()
                    elif soup.find('h1'):
                        product_name = soup.find('h1').text.strip()
                    elif soup.find('title'):
                        title_text = soup.find('title').text
                        product_name = title_text.split('-')[0].strip() if title_text else None

                    image_url = None
                    og_image_tag = soup.find('meta', property='og:image')
                    if og_image_tag and og_image_tag.get('content'):
                        image_url = og_image_tag['content']
                        logger.info(f"Found image via og:image tag: {image_url}")
                    if not image_url:
                        gallery = soup.find('div', class_='product-detail-galleria')
                        if gallery:
                            first_image = gallery.find('img')
                            if first_image and first_image.get('src'):
                                image_url = first_image['src']
                                logger.info(f"Found image via gallery container: {image_url}")

                    is_sold_out = "Tükendi" in html or "stok yok" in html.lower()
                    if soup.find('button', attrs={'data-testid': 'add-to-cart-button'}):
                        is_sold_out = False

                    if is_sold_out:
                        logger.info(f"Product is sold out: {product_name}")
                        return product_name, 0, image_url, "Tükendi"

                    price = None
                    price_container = soup.find('div', attrs={'data-testid': 'price'})
                    if price_container:
                        discounted_price = price_container.find('span', class_='price-view-discounted')
                        if discounted_price:
                            price = extract_price(discounted_price.text)
                    if not price:
                        script_tags = soup.find_all('script', type='application/ld+json')
                        for script in script_tags:
                            try:
                                data = json.loads(script.string)
                                if isinstance(data, dict) and 'offers' in data:
                                    offers = data['offers']
                                    if isinstance(offers, dict) and 'price' in offers:
                                        price = float(offers['price'])
                                        break
                                    elif isinstance(offers, list) and offers and 'price' in offers[0]:
                                        price = float(offers[0]['price'])
                                        break
                            except Exception:
                                continue

                    if not product_name:
                        return None, None, None, "Could not extract product name"
                    if not price:
                        logger.warning(f"Could not extract price for product: {product_name}")
                        return product_name, None, image_url, "Could not extract price"
                        
                    logger.info(f"Successfully scraped - Product: {product_name}, Price: {price} TL")
                    return product_name, price, image_url, None

            except asyncio.TimeoutError:
                last_error = "Timeout"
                logger.warning(f"Timeout for {url}, attempt {attempt + 1}")
            except aiohttp.ClientError as e:
                last_error = f"Client error: {str(e)}"
                logger.warning(f"Client error for {url}, attempt {attempt + 1}: {e}")
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.warning(f"Unexpected error for {url}, attempt {attempt + 1}: {e}")
        
        logger.error(f"All {MAX_RETRIES} attempts failed for {url}. Last error: {last_error}")
        return None, None, None, f"Failed after {MAX_RETRIES} attempts. Last error: {last_error}"
