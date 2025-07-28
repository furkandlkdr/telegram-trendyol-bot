import requests
from bs4 import BeautifulSoup
import re
from config import USER_AGENT
import logging
import json

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def is_valid_trendyol_url(url):
    """Check if the URL is a valid Trendyol URL."""
    return bool(re.match(r'https?://(www\.)?(trendyol\.com|ty\.gl|tyml\.gl|trendyol-milla\.com).*', url))

def get_full_url(url):
    """Follow redirects to get the full URL if it's a shortened link."""
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.head(url, headers=headers, allow_redirects=True)
        return response.url
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
    """Scrape product information from Trendyol."""
    try:
        # Follow redirects for shortened URLs
        full_url = get_full_url(url)
        
        # Check if the URL is a valid Trendyol URL
        if not is_valid_trendyol_url(full_url):
            return None, None, "URL does not belong to Trendyol"
        
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(full_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None, None, f"Failed to access the product page. Status code: {response.status_code}"
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # **YENİ: Ürün adı çekme - Güncel yapı**
        product_name = None
        
        # Method 1: YENİ Trendyol yapısı - h1 with data-testid
        h1_tag = soup.find('h1', attrs={'data-testid': 'product-name'})
        if h1_tag:
            product_name = h1_tag.text.strip()
        
        # Method 2: Genel h1 arama
        elif soup.find('h1'):
            product_name = soup.find('h1').text.strip()
        
        # Method 3: Title'dan çekme (fallback)
        elif soup.find('title'):
            title_text = soup.find('title').text
            product_name = title_text.split('-')[0].strip() if title_text else None
        
        # **YENİ: Stok kontrolü - Güncel yapı**
        is_sold_out = False
        stock_confirmed = False  # Pozitif stok kontrolü için flag
        
        # Method 1: YENİ - Add to cart button kontrolü (EN ÖNEMLİSİ)
        add_to_cart_btn = soup.find('button', attrs={'data-testid': 'add-to-cart-button'})
        if add_to_cart_btn:
            btn_text = add_to_cart_btn.get_text().strip()
            # Eğer buton "Sepete Ekle" yazıyorsa stokta var demektir
            if 'Sepete Ekle' in btn_text:
                is_sold_out = False
                stock_confirmed = True
                logger.info(f"Product is in stock - add to cart button found")
            elif 'Tükendi' in btn_text or 'Stok Yok' in btn_text or 'Mevcut Değil' in btn_text:
                is_sold_out = True
                stock_confirmed = True
                logger.info(f"Product is sold out - button indicates no stock")
        
        # Method 2: Buy now button kontrolü (güçlendirici)
        if not stock_confirmed:
            buy_now_btn = soup.find('button', class_='buy-now-button')
            if buy_now_btn:
                btn_text = buy_now_btn.get_text().strip()
                if 'Şimdi Al' in btn_text:
                    is_sold_out = False
                    stock_confirmed = True
                    logger.info(f"Product is in stock - buy now button found")
        
        # Method 3: Disabled button kontrolü (sadece pozitif kontrol yoksa)
        if not stock_confirmed:
            disabled_buttons = soup.find_all('button', disabled=True)
            for btn in disabled_buttons:
                btn_classes = btn.get('class', [])
                if any('add-to-cart' in str(cls) or 'sepete-ekle' in str(cls) for cls in btn_classes):
                    is_sold_out = True
                    stock_confirmed = True
                    logger.info("Product is sold out - add to cart button is disabled")
                    break
        
        # Method 4: Genel stok yokluğu mesajları (sadece pozitif kontrol yoksa)
        if not stock_confirmed:
            # Sadece görünür metin elementlerinde ara, JavaScript içeriğini ignore et
            visible_elements = soup.find_all(['div', 'span', 'p', 'h1', 'h2', 'h3', 'button'], 
                                           class_=lambda x: x and 'stock' in ' '.join(x).lower() if x else False)
            
            for element in visible_elements:
                text = element.get_text().strip().lower()
                if any(phrase in text for phrase in ['tükendi', 'stok yok', 'mevcut değil', 'satışta değil']):
                    # Ama JavaScript veya metadata değilse
                    if len(text) < 100 and not any(js_indicator in text for js_indicator in ['window', 'function', 'var ', '__']):
                        is_sold_out = True
                        stock_confirmed = True
                        logger.info(f"Sold out detected via visible text: {text}")
                        break
        
        if is_sold_out:
            logger.info(f"Product is sold out: {product_name}")
            return product_name, 0, "Tükendi"
        
        # **YENİ: Fiyat çekme - Güncel yapı**
        price = None
        
        # Method 1: YENİ - data-testid ile fiyat arama
        price_container = soup.find('div', attrs={'data-testid': 'price'})
        if price_container:
            logger.debug(f"Found price container: {price_container}")
            
            # İndirimli fiyat varsa onu al
            discounted_price = price_container.find('span', class_='price-view-discounted')
            if discounted_price:
                price = extract_price(discounted_price.text)
                logger.info(f"Found discounted price: {price}")
            
            # İndirimli fiyat yoksa normal fiyatı al
            if not price:
                original_price = price_container.find('span', class_='price-view-original')
                if original_price:
                    price = extract_price(original_price.text)
                    logger.info(f"Found original price: {price}")
            
            # price-view sınıfı olan herhangi bir span
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
            
            # Herhangi bir fiyat elementi varsa
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
        
        # Method 2: price-price sınıfı ile fiyat arama (yeni yapı)
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
        
        # Method 2: ESKİ yapı - campaign-price
        if not price:
            price_tag = soup.find('p', class_='campaign-price')
            if price_tag:
                price = extract_price(price_tag.text)
                logger.info(f"Found price via campaign-price: {price}")
        
        # Method 3: ESKİ yapı - prc-dsc
        if not price:
            price_tag = soup.find('span', class_='prc-dsc')
            if price_tag:
                price = extract_price(price_tag.text)
                logger.info(f"Found price via prc-dsc: {price}")
        
        # Method 4: JSON-LD structured data
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
        
        # Method 5: JavaScript variables (winnerVariant)
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
        
        # Method 6: Genel TL/₺ arama (son çare)
        if not price:
            price_elements = soup.find_all(string=re.compile(r'\d+[,.]?\d*\s*TL|\d+[,.]?\d*\s*₺'))
            for element in price_elements:
                # JavaScript içeriğini skip et
                parent = element.parent
                if parent and parent.name == 'script':
                    continue
                    
                extracted_price = extract_price(element)
                if extracted_price and 1 <= extracted_price <= 100000:  # Reasonable price range
                    price = extracted_price
                    logger.info(f"Found price via general TL search: {price}")
                    break
        # Sonuç kontrolü
        if not product_name:
            return None, None, "Could not extract product name"
            
        if not price:
            logger.warning(f"Could not extract price for product: {product_name}")
            return product_name, None, "Could not extract price"
            
        logger.info(f"Successfully scraped - Product: {product_name}, Price: {price} TL")
        return product_name, price, None
        
    except requests.RequestException as e:
        logger.error(f"Request error for {url}: {e}")
        return None, None, f"Request error: {str(e)}"
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return None, None, f"Error scraping product: {str(e)}"