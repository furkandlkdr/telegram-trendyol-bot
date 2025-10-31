import logging
import re
import time
import threading
import schedule
import traceback
from datetime import datetime
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from scraper import scrape_product_info, is_valid_trendyol_url
from data_manager import add_product, remove_product, get_all_products, update_product_price
from config import TELEGRAM_BOT_TOKEN, CHECK_INTERVAL, ALLOWED_GROUP_IDS, ADMIN_CHAT_ID, PRICE_CHANGE_THRESHOLD

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global variable to store bot instance
_bot_instance = None

def is_allowed_chat(chat_id):
    """Check if the chat_id is in the allowed list."""
    return chat_id in ALLOWED_GROUP_IDS

def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    chat_id = update.effective_chat.id
    
    # Check if the chat is allowed
    if not is_allowed_chat(chat_id):
        logger.info(f"Unauthorized start command from chat_id: {chat_id}")
        return
        
    update.message.reply_text(
        'Merhaba! Trendyol Fiyat Takip Botuna hoş geldiniz.\n\n'
        'Komutlar:\n'
        '/ekle [Trendyol linki] - Fiyat takibi için yeni bir ürün ekler\n'
        '/sil [Trendyol linki] - Takipten bir ürün çıkarır\n'
        '/listele - Takip edilen tüm ürünleri listeler\n'
        '/yenile - Tüm ürünlerin fiyatlarını manuel olarak kontrol eder\n\n'
        'Ayrıca, direkt olarak Trendyol.com veya ty.gl linki göndererek de ürün ekleyebilirsiniz.'
    )

def extract_url(text):
    """Extract URL from text."""
    url_pattern = r'https?://(?:www\.)?(trendyol\.com|ty\.gl|tyml\.gl|trendyol-milla\.com)[^\s]+'
    match = re.search(url_pattern, text)
    return match.group(0) if match else None

def add_product_handler(update: Update, context: CallbackContext):
    """Add a product to track."""
    chat_id = update.effective_chat.id
    
    # Check if the chat is allowed
    if not is_allowed_chat(chat_id):
        logger.info(f"Unauthorized add_product command from chat_id: {chat_id}")
        return
    
    # Extract URL from command or message text
    if context.args:
        url = extract_url(' '.join(context.args))
    else:
        update.message.reply_text('Lütfen geçerli bir Trendyol linki ekleyin.\n'
                                'Örnek: /ekle https://www.trendyol.com/...')
        return
    
    if not url or not is_valid_trendyol_url(url):
        update.message.reply_text('Geçerli bir Trendyol linki bulunamadı.')
        return
    
    # Send initial message
    message = update.message.reply_text('Ürün bilgileri alınıyor...')
    
    # Fetch product info
    product_name, price, error = scrape_product_info(url)
    
    if error == "Tükendi":
        # Handle sold out product
        success = add_product(chat_id, url, product_name, price)  # price is 0 for sold out products
        
        if success:
            message.edit_text(
                f'Ürün başarıyla eklendi!\n\n'
                f'Ürün: {product_name}\n'
                f'Durum: Tükendi\n\n'
                f'Ürün tekrar stokta olduğunda size bildirim göndereceğim.'
            )
        else:
            message.edit_text('Ürün eklenirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.')
        return
    elif error:
        message.edit_text(f'Hata: {error}')
        return
    
    if not price:
        message.edit_text('Ürün fiyatı alınamadı. Lütfen linki kontrol edin.')
        return
    
    # Add the product to tracking
    success = add_product(chat_id, url, product_name, price)
    
    if success:
        message.edit_text(
            f'Ürün başarıyla eklendi!\n\n'
            f'Ürün: {product_name}\n'
            f'Güncel Fiyat: {price:.2f} TL\n\n'
            f'Fiyat değiştiğinde size bildirim göndereceğim.'
        )
    else:
        message.edit_text('Ürün eklenirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.')

def url_handler(update: Update, context: CallbackContext):
    """Handle messages containing Trendyol URLs."""
    chat_id = update.effective_chat.id
    
    # Check if the chat is allowed
    if not is_allowed_chat(chat_id):
        logger.info(f"Unauthorized URL message from chat_id: {chat_id}")
        return
    
    # Extract URL from message text
    url = extract_url(update.message.text)
    
    if not url or not is_valid_trendyol_url(url):
        return  # Ignore non-Trendyol URLs
    
    # Send initial message
    message = update.message.reply_text('Ürün bilgileri alınıyor...')
    
    # Fetch product info
    product_name, price, error = scrape_product_info(url)
    
    if error == "Tükendi":
        # Handle sold out product
        success = add_product(chat_id, url, product_name, price)  # price is 0 for sold out products
        
        if success:
            message.edit_text(
                f'Ürün başarıyla eklendi!\n\n'
                f'Ürün: {product_name}\n'
                f'Durum: Tükendi\n\n'
                f'Ürün tekrar stokta olduğunda size bildirim göndereceğim.'
            )
        else:
            message.edit_text('Ürün eklenirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.')
        return
    elif error:
        message.edit_text(f'Hata: {error}')
        return
    
    if not price:
        message.edit_text('Ürün fiyatı alınamadı. Lütfen linki kontrol edin.')
        return
    
    # Add the product to tracking
    success = add_product(chat_id, url, product_name, price)
    
    if success:
        message.edit_text(
            f'Ürün başarıyla eklendi!\n\n'
            f'Ürün: {product_name}\n'
            f'Güncel Fiyat: {price:.2f} TL\n\n'
            f'Fiyat değiştiğinde size bildirim göndereceğim.'
        )
    else:
        message.edit_text('Ürün eklenirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.')

def remove_product_handler(update: Update, context: CallbackContext):
    """Remove a product from tracking."""
    chat_id = update.effective_chat.id
    
    # Check if the chat is allowed
    if not is_allowed_chat(chat_id):
        logger.info(f"Unauthorized remove_product command from chat_id: {chat_id}")
        return
    
    # Extract URL from command
    if context.args:
        url = extract_url(' '.join(context.args))
    else:
        update.message.reply_text('Lütfen silmek istediğiniz ürünün Trendyol linkini ekleyin.\n'
                                'Örnek: /sil https://www.trendyol.com/...')
        return
    
    if not url:
        update.message.reply_text('Geçerli bir Trendyol linki bulunamadı.')
        return
    
    # Remove the product from tracking
    success = remove_product(chat_id, url)
    
    if success:
        update.message.reply_text('Ürün takipten çıkarıldı.')
    else:
        update.message.reply_text('Ürün bulunamadı veya zaten takip edilmiyor.')

def list_products(update: Update, context: CallbackContext):
    """List all tracked products."""
    chat_id = update.effective_chat.id
    
    # Check if the chat is allowed
    if not is_allowed_chat(chat_id):
        logger.info(f"Unauthorized list_products command from chat_id: {chat_id}")
        return
    
    # Get all products for this chat
    products = get_all_products(chat_id)
    
    if not products:
        update.message.reply_text('Henüz takip edilen ürün bulunmamaktadır.')
        return
    
    # Prepare the message text
    message = 'Takip Edilen Ürünler:\n\n'
    
    for url, product_info in products.items():
        product_name = product_info.get('product_name', 'İsimsiz Ürün')
        current_price = product_info.get('current_price', 0)
        initial_price = product_info.get('initial_price', 0)
        
        # Check if product is sold out (price is 0)
        if current_price == 0:
            message += (
                f'🔹 <b>{product_name}</b>\n'
                f'   <b>Tükendi</b>\n'
                f'   <a href="{url}">Link</a>\n\n'
            )
            continue
        
        price_diff = current_price - initial_price
        if price_diff > 0:
            price_trend = f'📈 +{price_diff:.2f} TL'
        elif price_diff < 0:
            price_trend = f'📉 {price_diff:.2f} TL'
        else:
            price_trend = '➡️ Değişim yok'
        
        message += (
            f'🔹 <b>{product_name}</b>\n'
            f'   Güncel Fiyat: <b>{current_price:.2f} TL</b> {price_trend}\n'
            f'   <a href="{url}">Link</a>\n\n'
        )
    
    update.message.reply_text(message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

# Global variable to store bot instance
_bot_instance = None

def check_prices():
    """Check prices for all tracked products and notify if there's a change."""
    global _bot_instance
    
    if not _bot_instance:
        logger.error("Bot instance not available for price checking")
        return
        
    data = get_all_products()
    
    if not data:
        logger.info("No products to check")
        return
    
    error_count = 0
    
    for chat_id, products in data.items():
        for url, product_info in list(products.items()):
            try:
                product_name = product_info['product_name']
                current_price = product_info['current_price']
                
                logger.info(f"Checking price for {product_name} at {url}")
                
                # Fetch new product info
                _, new_price, error = scrape_product_info(url)
                
                # Handle sold-out products specially
                if error == "Tükendi":
                    # Product is sold out
                    if current_price != 0:  # Only update if not already marked as sold out
                        update_product_price(chat_id, url, 0)
                        
                        # Send sold-out notification
                        notification_text = (
                            f'🚫 <b>Ürün Tükendi!</b>\n\n'
                            f'<b>{product_name}</b>\n'
                            f'Eski Fiyat: <b>{current_price:.2f} TL</b>\n'
                            f'Durum: <b>Stoklar Tükendi</b>\n\n'
                            f'Ürün tekrar stokta olduğunda bildirim göndereceğim.\n\n'
                            f'<a href="{url}">Ürüne Git</a>'
                        )
                        
                        try:
                            _bot_instance.send_message(
                                chat_id=int(chat_id),
                                text=notification_text,
                                parse_mode=ParseMode.HTML,
                                disable_web_page_preview=True
                            )
                            logger.info(f"Sold-out notification sent to {chat_id}")
                        except Exception as send_error:
                            logger.error(f"Failed to send sold-out notification to {chat_id}: {send_error}")
                            error_count += 1
                    else:
                        logger.info(f"Product {product_name} is still sold out")
                    continue
                
                if error:
                    logger.error(f"Error checking {url}: {error}")
                    error_count += 1
                    continue
                
                # Handle case where product was sold out but now has a price (back in stock)
                if current_price == 0 and new_price and new_price > 0:
                    # Product is back in stock!
                    update_product_price(chat_id, url, new_price)
                    
                    notification_text = (
                        f'🟢 <b>Ürün Tekrar Stokta!</b>\n\n'
                        f'<b>{product_name}</b>\n'
                        f'Yeni Fiyat: <b>{new_price:.2f} TL</b>\n\n'
                        f'<a href="{url}">Ürüne Git</a>'
                    )
                    
                    try:
                        _bot_instance.send_message(
                            chat_id=int(chat_id),
                            text=notification_text,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True
                        )
                        logger.info(f"Back-in-stock notification sent to {chat_id}")
                    except Exception as send_error:
                        logger.error(f"Failed to send back-in-stock notification to {chat_id}: {send_error}")
                        error_count += 1
                    continue
                
                if new_price is None:
                    logger.error(f"Could not get price for {url}")
                    error_count += 1
                    continue
                
                # If the price has changed
                if abs(new_price - current_price) > 0.01:  # Allow for small decimal differences
                    # Safety check to prevent division by zero
                    if current_price == 0:
                        logger.warning(f"Unexpected zero price for {product_name}, skipping percentage calculation")
                        continue
                    
                    # Calculate percentage change
                    percentage_change = abs((new_price - current_price) / current_price * 100)
                    
                    # Only send notification if the change is more than the threshold
                    if percentage_change > PRICE_CHANGE_THRESHOLD:
                        # Update the price in the database
                        update_product_price(chat_id, url, new_price)
                        
                        # Prepare and send notification
                        price_diff = new_price - current_price
                        if price_diff > 0:
                            trend_emoji = "📈 Fiyat Yükseldi"
                            trend_color = "🔴"
                        else:
                            trend_emoji = "📉 Fiyat Düştü"
                            trend_color = "🟢"
                        
                        notification_text = (
                            f'{trend_color} <b>{trend_emoji}!</b>\n\n'
                            f'<b>{product_name}</b>\n'
                            f'Eski Fiyat: <b>{current_price:.2f} TL</b>\n'
                            f'Yeni Fiyat: <b>{new_price:.2f} TL</b>\n'
                            f'Fark: <b>{price_diff:+.2f} TL (%{(price_diff/current_price*100):+.1f})</b>\n\n'
                            f'<a href="{url}">Ürüne Git</a>'
                        )
                        
                        # Send notification
                        try:
                            _bot_instance.send_message(
                                chat_id=int(chat_id),
                                text=notification_text,
                                parse_mode=ParseMode.HTML,
                                disable_web_page_preview=True
                            )
                            logger.info(f"Price change notification sent to {chat_id}")
                        except Exception as send_error:
                            logger.error(f"Failed to send notification to {chat_id}: {send_error}")
                            error_count += 1
                    else:
                        # Price changed but not enough to notify - still update the database
                        update_product_price(chat_id, url, new_price)
                        logger.info(f"Price change for {product_name} ({percentage_change:.2f}%) is below threshold ({PRICE_CHANGE_THRESHOLD}%), no notification sent")
                else:
                    logger.info(f"No price change for {product_name}")
            
            except Exception as e:
                logger.error(f"Error checking price for {url}: {e}")
                error_count += 1
    
    # Send admin notification if there are too many errors
    if error_count > 5 and ADMIN_CHAT_ID:
        total_products = sum(len(products) for products in data.values())
        error_rate = (error_count / total_products) * 100 if total_products > 0 else 0
        
        admin_message = f"""
⚠️ <b>Fiyat Kontrol Uyarısı</b>

<b>Zaman:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
<b>Toplam Ürün:</b> {total_products}
<b>Hata Sayısı:</b> {error_count}
<b>Hata Oranı:</b> %{error_rate:.1f}

<b>Durum:</b> Çok sayıda hata tespit edildi
<b>Olası Sebepler:</b>
• Ağ bağlantı sorunları
• Trendyol anti-bot korumaları
• Site yapısı değişiklikleri
• Sunucu yük problemi

<b>Öneriler:</b>
• İnternet bağlantısını kontrol edin
• Birkaç dakika bekleyip tekrar deneyin
• Bot'u yeniden başlatmayı deneyin
        """
        send_admin_notification(admin_message)

def run_scheduler():
    """Run the scheduler in a separate thread."""
    while True:
        schedule.run_pending()
        time.sleep(1)

def send_admin_notification(message):
    """Send notification to admin chat."""
    global _bot_instance
    
    if not _bot_instance or not ADMIN_CHAT_ID:
        return False
        
    try:
        _bot_instance.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")
        return False

def error(update: Update, context: CallbackContext):
    """Log errors caused by updates and notify admin."""
    error_message = str(context.error)
    error_type = type(context.error).__name__
    
    # Log the error with more detail
    logger.error(f"Update {update} caused error {error_type}: {error_message}")
    logger.error(f"Full traceback: {traceback.format_exc()}")
    
    # Prepare detailed error message for admin
    if ADMIN_CHAT_ID:
        try:
            # Check for specific error types
            error_category = "Genel Hata"
            if "urllib3" in error_message or "HTTPError" in error_message:
                error_category = "Ağ Bağlantı Hatası"
            elif "timeout" in error_message.lower():
                error_category = "Zaman Aşımı Hatası"
            elif "connection" in error_message.lower():
                error_category = "Bağlantı Hatası"
            elif "remote" in error_message.lower() and "disconnect" in error_message.lower():
                error_category = "Sunucu Bağlantı Hatası"
            
            admin_message = f"""
🚨 <b>Trendyol Bot Hatası</b>

<b>Kategori:</b> {error_category}
<b>Hata Türü:</b> <code>{error_type}</code>
<b>Hata:</b> <code>{error_message}</code>

<b>Zaman:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

<b>Update:</b> <code>{str(update)[:500] if update else 'None'}</code>

<b>Traceback:</b>
<pre>{traceback.format_exc()[:1000]}</pre>

<b>Önerilen Çözüm:</b>
{get_error_solution(error_category)}
            """
            
            send_admin_notification(admin_message)
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
    
    # Notify user about the error if possible
    if update and update.effective_message:
        try:
            update.effective_message.reply_text('Bir hata oluştu. Lütfen daha sonra tekrar deneyin.')
        except:
            pass  # Ignore if we can't send user notification

def get_error_solution(error_category):
    """Get suggested solution based on error category."""
    solutions = {
        "Ağ Bağlantı Hatası": "• İnternet bağlantısını kontrol edin\n• Birkaç dakika bekleyip tekrar deneyin\n• Trendyol sitesinin erişilebilir olduğunu kontrol edin",
        "Zaman Aşımı Hatası": "• Timeout değerini artırın\n• İnternet hızını kontrol edin\n• Sunucu yükü yüksek olabilir",
        "Bağlantı Hatası": "• DNS ayarlarını kontrol edin\n• VPN kullanıyorsanız kapatıp deneyin\n• Firewall ayarlarını kontrol edin",
        "Sunucu Bağlantı Hatası": "• Trendyol sunucularında sorun olabilir\n• Biraz bekleyip tekrar deneyin\n• İstek sıklığını azaltın",
        "Genel Hata": "• Logları kontrol edin\n• Bot'u yeniden başlatmayı deneyin\n• Gerekirse manual müdahale edin"
    }
    return solutions.get(error_category, "• Logları kontrol edin\n• Gerekirse yeniden başlatın")

def main():
    """Start the bot."""
    global _bot_instance
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("No token provided. Set TELEGRAM_BOT_TOKEN in .env file.")
        return
        
    if not ALLOWED_GROUP_IDS:
        logger.warning("ALLOWED_GROUP_IDS is not set in .env file. Bot will not respond to any group.")
        logger.warning("Set ALLOWED_GROUP_IDS with comma-separated group IDs in your .env file.")
    
    # Create the Updater and pass it the bot's token
    updater = Updater(TELEGRAM_BOT_TOKEN)
    
    # Store bot instance globally for price checking
    _bot_instance = updater.bot
    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("ekle", add_product_handler))
    dispatcher.add_handler(CommandHandler("sil", remove_product_handler))
    dispatcher.add_handler(CommandHandler("listele", list_products))
    dispatcher.add_handler(CommandHandler("yenile", refresh_prices_handler))
    
    # Message handler for Trendyol links
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command & Filters.regex(r'https?://(www\.)?(trendyol\.com|ty\.gl|tyml\.gl|trendyol-milla\.com)'), 
        url_handler
    ))
    
    # Error handler
    dispatcher.add_error_handler(error)
    
    # Clear any existing scheduled jobs to prevent duplicates
    schedule.clear()
    
    # Schedule price checking based on the defined interval
    schedule.every(CHECK_INTERVAL).minutes.do(check_prices)
    
    # Start the scheduler in a new thread
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # Start the Bot
    updater.start_polling()
    logger.info("Bot started!")
    
    # Run the bot until the user presses Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()

def refresh_prices_handler(update: Update, context: CallbackContext):
    """Manual refresh command to check all tracked products immediately."""
    chat_id = update.effective_chat.id
    
    # Check if the chat is allowed
    if not is_allowed_chat(chat_id):
        logger.info(f"Unauthorized refresh command from chat_id: {chat_id}")
        return
    
    # Get products for this specific chat
    products = get_all_products(chat_id)
    
    if not products:
        update.message.reply_text('Henüz takip edilen ürün bulunmamaktadır.')
        return
    
    # Send initial message
    message = update.message.reply_text(f'🔄 Fiyatlar kontrol ediliyor... ({len(products)} ürün)')
    
    checked_count = 0
    changed_count = 0
    error_count = 0
    
    for url, product_info in products.items():
        try:
            product_name = product_info['product_name']
            current_price = product_info['current_price']
            
            # Fetch new product info
            _, new_price, error = scrape_product_info(url)
            
            # Handle sold-out products specially
            if error == "Tükendi":
                # Product is sold out
                checked_count += 1
                if current_price != 0:  # Only update if not already marked as sold out
                    changed_count += 1
                    update_product_price(chat_id, url, 0)  # Mark as sold out with price 0
                    
                    # Send sold-out notification
                    notification_text = (
                        f'🚫 <b>Ürün Tükendi! (Manuel Kontrol)</b>\n\n'
                        f'<b>{product_name}</b>\n'
                        f'Eski Fiyat: <b>{current_price:.2f} TL</b>\n'
                        f'Durum: <b>Stoklar Tükendi</b>\n\n'
                        f'Ürün tekrar stokta olduğunda bildirim göndereceğim.\n\n'
                        f'<a href="{url}">Ürüne Git</a>'
                    )
                    
                    try:
                        context.bot.send_message(
                            chat_id=chat_id,
                            text=notification_text,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True
                        )
                        logger.info(f"Manual sold-out notification sent to {chat_id}")
                    except Exception as send_error:
                        logger.error(f"Failed to send notification to {chat_id}: {send_error}")
                        error_count += 1
                continue
            
            if error:
                logger.error(f"Error checking {url}: {error}")
                error_count += 1
                continue
            
            # Handle case where product was sold out but now has a price (back in stock)
            if current_price == 0 and new_price and new_price > 0:
                # Product is back in stock!
                checked_count += 1
                changed_count += 1
                update_product_price(chat_id, url, new_price)
                
                notification_text = (
                    f'🟢 <b>Ürün Tekrar Stokta! (Manuel Kontrol)</b>\n\n'
                    f'<b>{product_name}</b>\n'
                    f'Yeni Fiyat: <b>{new_price:.2f} TL</b>\n\n'
                    f'<a href="{url}">Ürüne Git</a>'
                )
                
                try:
                    context.bot.send_message(
                        chat_id=chat_id,
                        text=notification_text,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                    logger.info(f"Manual back-in-stock notification sent to {chat_id}")
                except Exception as send_error:
                    logger.error(f"Failed to send notification to {chat_id}: {send_error}")
                    error_count += 1
                continue
            
            if new_price is None:
                logger.error(f"Could not get price for {url}")
                error_count += 1
                continue
            
            checked_count += 1
            
            # If the price has changed
            if abs(new_price - current_price) > 0.01:  # Allow for small decimal differences
                # Safety check to prevent division by zero
                if current_price == 0:
                    logger.warning(f"Unexpected zero price for {product_name}, skipping percentage calculation")
                    continue
                
                # Calculate percentage change
                percentage_change = abs((new_price - current_price) / current_price * 100)
                
                # Only send notification if the change is more than the threshold
                if percentage_change > PRICE_CHANGE_THRESHOLD:
                    changed_count += 1
                    
                    # Update the price in the database
                    update_product_price(chat_id, url, new_price)
                    
                    # Prepare and send notification
                    price_diff = new_price - current_price
                    if price_diff > 0:
                        trend_emoji = "📈 Fiyat Yükseldi"
                        trend_color = "🔴"
                    else:
                        trend_emoji = "📉 Fiyat Düştü"
                        trend_color = "🟢"
                    
                    notification_text = (
                        f'{trend_color} <b>{trend_emoji}! (Manuel Kontrol)</b>\n\n'
                        f'<b>{product_name}</b>\n'
                        f'Eski Fiyat: <b>{current_price:.2f} TL</b>\n'
                        f'Yeni Fiyat: <b>{new_price:.2f} TL</b>\n'
                        f'Fark: <b>{price_diff:+.2f} TL (%{(price_diff/current_price*100):+.1f})</b>\n\n'
                        f'<a href="{url}">Ürüne Git</a>'
                    )
                    
                    # Send notification immediately
                    try:
                        context.bot.send_message(
                            chat_id=chat_id,
                            text=notification_text,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True
                        )
                        logger.info(f"Manual price change notification sent to {chat_id}")
                    except Exception as send_error:
                        logger.error(f"Failed to send notification to {chat_id}: {send_error}")
                        error_count += 1
                else:
                    # Price changed but not enough to notify - still update the database
                    update_product_price(chat_id, url, new_price)
                    logger.info(f"Price change for {product_name} ({percentage_change:.2f}%) is below threshold ({PRICE_CHANGE_THRESHOLD}%), no notification sent")
        
        except Exception as e:
            logger.error(f"Error checking price for {url}: {e}")
            error_count += 1
    
    # Update the status message with results
    if error_count > 0:
        status_emoji = "⚠️"
        status_text = f"tamamlandı (bazı hatalarla)"
    else:
        status_emoji = "✅"
        status_text = "tamamlandı"
    
    final_message = (
        f'{status_emoji} <b>Fiyat kontrolü {status_text}</b>\n\n'
        f'📊 <b>Özet:</b>\n'
        f'• Toplam ürün: {len(products)}\n'
        f'• Kontrol edilen: {checked_count}\n'
        f'• Fiyat değişen: {changed_count}\n'
        f'• Hata: {error_count}\n\n'
        f'💡 Otomatik kontrol {CHECK_INTERVAL} dakikada bir yapılmaktadır.'
    )
    
    message.edit_text(final_message, parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    main()

