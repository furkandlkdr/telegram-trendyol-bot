import logging
import re
import asyncio
import schedule
import traceback
from datetime import datetime
import discord
from discord.ext import commands
from scraper import scrape_product_info, is_valid_trendyol_url
from data_manager import add_product, remove_product, get_all_products, update_product_price
from config import DISCORD_BOT_TOKEN, CHECK_INTERVAL, ADMIN_USER_ID

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

# Create bot instance
bot = commands.Bot(command_prefix='/', intents=intents)

def extract_url(text):
    """Extract URL from text."""
    url_pattern = r'https?://(?:www\.)?(trendyol\.com|ty\.gl|tyml\.gl|trendyol-milla\.com)[^\s]+'
    match = re.search(url_pattern, text)
    return match.group(0) if match else None

async def send_admin_notification(message):
    """Send notification to admin user."""
    if not ADMIN_USER_ID:
        return False

    try:
        admin = await bot.fetch_user(int(ADMIN_USER_ID))
        if admin:
            await admin.send(embed=discord.Embed.from_dict({"title": "Admin Notification", "description": message, "color": 0xff0000}))
            return True
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")
        return False

@bot.event
async def on_ready():
    """Event triggered when the bot is ready."""
    logger.info(f'Logged in as {bot.user.name}')
    logger.info("Bot is ready and running!")
    # Start the scheduler
    schedule.every(CHECK_INTERVAL).minutes.do(lambda: asyncio.run_coroutine_threadsafe(check_prices(), bot.loop))
    # Run scheduler in a separate thread
    loop = asyncio.get_event_loop()
    loop.create_task(run_scheduler())

async def run_scheduler():
    """Run the scheduler."""
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

@bot.command(name='start', aliases=['yardim'])
async def start(ctx):
    """Send a welcome message."""
    embed = discord.Embed(
        title='Merhaba! Trendyol Fiyat Takip Botuna hoş geldiniz.',
        description='Komutlar:\n'
                    '`/ekle [Trendyol linki]` - Fiyat takibi için yeni bir ürün ekler\n'
                    '`/sil [Trendyol linki]` - Takipten bir ürün çıkarır\n'
                    '`/listele` - Takip edilen tüm ürünleri listeler\n'
                    '`/yenile` - Tüm ürünlerin fiyatlarını manuel olarak kontrol eder\n\n'
                    'Ayrıca, direkt olarak Trendyol.com veya ty.gl linki göndererek de ürün ekleyebilirsiniz.',
        color=0x00ff00
    )
    await ctx.send(embed=embed)

@bot.command(name='ekle')
async def add_product_handler(ctx, *, url: str = None):
    """Add a product to track."""
    if url is None:
        await ctx.send('Lütfen geçerli bir Trendyol linki ekleyin.\n'
                       'Örnek: /ekle https://www.trendyol.com/...')
        return

    url = extract_url(url)
    if not url or not is_valid_trendyol_url(url):
        await ctx.send('Geçerli bir Trendyol linki bulunamadı.')
        return

    message = await ctx.send('Ürün bilgileri alınıyor...')
    
    product_name, price, error = scrape_product_info(url)
    
    if error:
        await message.edit(content=f'Hata: {error}')
        return
    
    if not price:
        await message.edit(content='Ürün fiyatı alınamadı. Lütfen linki kontrol edin.')
        return
    
    success = add_product(ctx.channel.id, url, product_name, price)
    
    if success:
        embed = discord.Embed(
            title='Ürün Başarıyla Eklendi!',
            description=f'**Ürün:** {product_name}\n'
                        f'**Güncel Fiyat:** {price:.2f} TL\n\n'
                        f'Fiyat değiştiğinde size bildirim göndereceğim.',
            color=0x00ff00
        )
        await message.edit(content=None, embed=embed)
    else:
        await message.edit(content='Ürün eklenirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.')

@bot.command(name='sil')
async def remove_product_handler(ctx, *, url: str = None):
    """Remove a product from tracking."""
    if url is None:
        await ctx.send('Lütfen silmek istediğiniz ürünün Trendyol linkini ekleyin.\n'
                       'Örnek: /sil https://www.trendyol.com/...')
        return

    url = extract_url(url)
    if not url:
        await ctx.send('Geçerli bir Trendyol linki bulunamadı.')
        return

    success = remove_product(ctx.channel.id, url)
    
    if success:
        await ctx.send('Ürün takipten çıkarıldı.')
    else:
        await ctx.send('Ürün bulunamadı veya zaten takip edilmiyor.')

@bot.command(name='listele')
async def list_products(ctx):
    """List all tracked products."""
    products = get_all_products(ctx.channel.id)
    
    if not products:
        await ctx.send('Henüz takip edilen ürün bulunmamaktadır.')
        return

    embed = discord.Embed(title='Takip Edilen Ürünler', color=0x00ff00)
    
    for url, product_info in products.items():
        product_name = product_info.get('product_name', 'İsimsiz Ürün')
        current_price = product_info.get('current_price', 0)
        
        if current_price == 0:
            embed.add_field(name=product_name, value=f'**Tükendi**\n[Link]({url})', inline=False)
            continue
        
        initial_price = product_info.get('initial_price', 0)
        price_diff = current_price - initial_price

        if price_diff > 0:
            price_trend = f'📈 +{price_diff:.2f} TL'
        elif price_diff < 0:
            price_trend = f'📉 {price_diff:.2f} TL'
        else:
            price_trend = '➡️ Değişim yok'

        embed.add_field(
            name=product_name,
            value=f'**Güncel Fiyat:** {current_price:.2f} TL {price_trend}\n[Link]({url})',
            inline=False
        )

    await ctx.send(embed=embed)

@bot.command(name='yenile')
async def refresh_prices_handler(ctx):
    """Manual refresh command to check all tracked products immediately."""
    products = get_all_products(ctx.channel.id)
    
    if not products:
        await ctx.send('Henüz takip edilen ürün bulunmamaktadır.')
        return

    message = await ctx.send(f'🔄 Fiyatlar kontrol ediliyor... ({len(products)} ürün)')

    checked_count = 0
    changed_count = 0
    error_count = 0

    for url, product_info in products.items():
        try:
            product_name = product_info['product_name']
            current_price = product_info['current_price']

            _, new_price, error = scrape_product_info(url)

            if error:
                error_count += 1
                continue

            if new_price is None:
                error_count += 1
                continue

            checked_count += 1

            if abs(new_price - current_price) > 0.01:
                changed_count += 1
                update_product_price(ctx.channel.id, url, new_price)

                price_diff = new_price - current_price
                trend_emoji = "📈 Fiyat Yükseldi" if price_diff > 0 else "📉 Fiyat Düştü"

                notification_embed = discord.Embed(
                    title=f'{trend_emoji}!',
                    description=f'**{product_name}**\n'
                                f'**Eski Fiyat:** {current_price:.2f} TL\n'
                                f'**Yeni Fiyat:** {new_price:.2f} TL\n'
                                f'**Fark:** {price_diff:+.2f} TL (%{(price_diff/current_price*100):+.1f})\n\n'
                                f'[Ürüne Git]({url})',
                    color=0xff0000 if price_diff > 0 else 0x00ff00
                )
                await ctx.send(embed=notification_embed)
        
        except Exception as e:
            error_count += 1
            logger.error(f"Error checking price for {url}: {e}")

    status_emoji = "⚠️" if error_count > 0 else "✅"
    status_text = f"tamamlandı (bazı hatalarla)" if error_count > 0 else "tamamlandı"

    final_embed = discord.Embed(
        title=f'{status_emoji} Fiyat kontrolü {status_text}',
        description=f'📊 **Özet:**\n'
                    f'• Toplam ürün: {len(products)}\n'
                    f'• Kontrol edilen: {checked_count}\n'
                    f'• Fiyat değişen: {changed_count}\n'
                    f'• Hata: {error_count}\n\n'
                    f'💡 Otomatik kontrol {CHECK_INTERVAL} dakikada bir yapılmaktadır.',
        color=0xffa500 if error_count > 0 else 0x00ff00
    )

    await message.edit(content=None, embed=final_embed)

async def check_prices():
    """Check prices for all tracked products and notify if there's a change."""
    data = get_all_products()
    
    if not data:
        logger.info("No products to check")
        return
    
    error_count = 0
    
    for channel_id, products in data.items():
        for url, product_info in list(products.items()):
            try:
                product_name = product_info['product_name']
                current_price = product_info['current_price']
                
                logger.info(f"Checking price for {product_name} at {url}")
                
                _, new_price, error = scrape_product_info(url)
                
                if error:
                    logger.error(f"Error checking {url}: {error}")
                    error_count += 1
                    continue
                
                if new_price is None:
                    logger.error(f"Could not get price for {url}")
                    error_count += 1
                    continue
                
                if abs(new_price - current_price) > 0.01:
                    update_product_price(channel_id, url, new_price)
                    
                    price_diff = new_price - current_price
                    trend_emoji = "📈 Fiyat Yükseldi" if price_diff > 0 else "📉 Fiyat Düştü"
                    
                    notification_embed = discord.Embed(
                        title=f'{trend_emoji}!',
                        description=f'**{product_name}**\n'
                                    f'**Eski Fiyat:** {current_price:.2f} TL\n'
                                    f'**Yeni Fiyat:** {new_price:.2f} TL\n'
                                    f'**Fark:** {price_diff:+.2f} TL (%{(price_diff/current_price*100):+.1f})\n\n'
                                    f'[Ürüne Git]({url})',
                        color=0xff0000 if price_diff > 0 else 0x00ff00
                    )
                    
                    try:
                        channel = await bot.fetch_channel(int(channel_id))
                        await channel.send(embed=notification_embed)
                        logger.info(f"Price change notification sent to {channel_id}")
                    except Exception as send_error:
                        logger.error(f"Failed to send notification to {channel_id}: {send_error}")
                        error_count += 1
                else:
                    logger.info(f"No price change for {product_name}")
            
            except Exception as e:
                logger.error(f"Error checking price for {url}: {e}")
                error_count += 1
    
    if error_count > 5 and ADMIN_USER_ID:
        total_products = sum(len(products) for products in data.values())
        error_rate = (error_count / total_products) * 100 if total_products > 0 else 0
        
        admin_message = f"**Fiyat Kontrol Uyarısı**\n" \
                        f"**Zaman:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n" \
                        f"**Toplam Ürün:** {total_products}\n" \
                        f"**Hata Sayısı:** {error_count}\n" \
                        f"**Hata Oranı:** %{error_rate:.1f}"
        
        await send_admin_notification(admin_message)

@bot.event
async def on_message(message):
    """Handle messages containing Trendyol URLs."""
    if message.author == bot.user:
        return

    url = extract_url(message.content)
    
    if url and is_valid_trendyol_url(url):
        # Acknowledge the command, as it's processed by the bot
        await bot.process_commands(message)
        if message.content.startswith(bot.command_prefix):
             return

        msg = await message.channel.send('Ürün bilgileri alınıyor...')

        product_name, price, error = scrape_product_info(url)

        if error:
            await msg.edit(content=f'Hata: {error}')
            return

        if not price:
            await msg.edit(content='Ürün fiyatı alınamadı. Lütfen linki kontrol edin.')
            return

        success = add_product(message.channel.id, url, product_name, price)

        if success:
            embed = discord.Embed(
                title='Ürün Başarıyla Eklendi!',
                description=f'**Ürün:** {product_name}\n'
                            f'**Güncel Fiyat:** {price:.2f} TL\n\n'
                            f'Fiyat değiştiğinde size bildirim göndereceğim.',
                color=0x00ff00
            )
            await msg.edit(content=None, embed=embed)
        else:
            await msg.edit(content='Ürün eklenirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.')
    else:
        await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.CommandNotFound):
        return
    logger.error(f"An error occurred: {error}")
    await ctx.send("Bir hata oluştu. Lütfen daha sonra tekrar deneyin.")

def main():
    """Start the bot."""
    if not DISCORD_BOT_TOKEN:
        logger.error("No token provided. Set DISCORD_BOT_TOKEN in .env file.")
        return
    
    bot.run(DISCORD_BOT_TOKEN)

if __name__ == '__main__':
    main()
