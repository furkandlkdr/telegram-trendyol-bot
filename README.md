# [EN] Trendyol Price Tracking Bot

An advanced Telegram bot that tracks product prices on Trendyol and sends smart notifications when prices change. Designed for efficiency and reliability with enhanced user experience.

## ✨ Features

### Core Features
- 🔗 **Universal Link Support**: Works with Trendyol.com, ty.gl (shortened), tyml.gl, and trendyol-milla.com links
- ➕ **Easy Product Addition**: Use `/ekle` command or simply send a Trendyol link
- ➖ **Product Management**: Remove products with `/sil` command
- 📋 **Smart Listing**: View all tracked products with price trends using `/listele`
- 🔄 **Automated Price Monitoring**: Configurable interval-based price checking
- 🎯 **Smart Notifications**: 
  - 📈 "Price Increased" notifications with red indicator
  - 📉 "Price Decreased" notifications with green indicator
  - Detailed price difference and percentage change
  - 🔔 Customizable notification threshold per chat
- 🔄 **Manual Refresh**: Use `/yenile` command to instantly check all product prices

### Advanced Features
- 🛒 **Sold-Out Product Tracking**: 
  - Automatic detection of out-of-stock products
  - Special notifications when products go out of stock
  - Back-in-stock alerts when products become available again
- ⚙️ **Dynamic Price Threshold**: 
  - Set custom price change threshold per chat with `/threshold` command
  - Only get notified when price changes exceed your threshold
  - Prevents notification spam for minor price fluctuations
- 🏠 **Multi-Group Support**: Restrict bot access to specific Telegram groups
- 🚨 **Advanced Error Handling & Monitoring**:
  - Automatic admin notifications for critical errors
  - Categorized error messages with suggested solutions
  - High error rate detection and alerts
  - Detailed logging for debugging
- ⚡ **Optimized Performance**: Lightweight code perfect for Raspberry Pi and low-power devices
- 🎨 **Rich Formatting**: HTML-formatted messages with clickable links

### Anti-Bot & Reliability Features
- 🔄 **Smart Retry Strategy**: Automatic retry with exponential backoff on failures
- ⏱️ **Random Request Delays**: Anti-bot protection with randomized delays between requests
- 🔌 **Connection Pooling**: Efficient HTTP session management with connection reuse
- 🎯 **Multiple Scraping Methods**: 7 different fallback methods for price detection
- 📊 **JSON-LD Support**: Extract prices from structured data when available
- 🧩 **JavaScript Parsing**: Can extract prices from JavaScript variables when needed

## 📋 Requirements

- **Python 3.6+** (Recommended: Python 3.8 or newer)
- **pip** (Python package manager)
- **Telegram Bot Token** (obtainable from [@BotFather](https://t.me/botfather))
- **Telegram Group ID(s)** for access control

## 🚀 Installation

### Quick Setup

1. **Clone the repository:**
```bash
git clone https://github.com/furkandlkdr/telegram-trendyol-bot.git
cd telegram-trendyol-bot
```

2. **Create and activate virtual environment:**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**
   - Copy `.env.example` to `.env`
   - Edit `.env` with your settings:

```env
# Telegram Bot Token from @BotFather
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Price check interval in minutes (default: 30)
CHECK_INTERVAL=30

# Comma-separated list of allowed Telegram group IDs
ALLOWED_GROUP_IDS=-1001234567890,-1009876543210
```

5. **Start the bot:**
```bash
python main.py
```

## 🔧 Getting Group ID

To find your Telegram group ID:

1. Add the bot to your group
2. Send any message in the group
3. Visit: `https://api.telegram.org/bot{YOUR_BOT_TOKEN}/getUpdates`
4. Look for `"chat":{"id": -1001234567890}` in the JSON response
5. Copy the negative number (including the minus sign)

## 📖 Usage Guide

### Basic Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Initialize bot and show help | `/start` |
| `/ekle [URL]` | Add product to tracking | `/ekle https://www.trendyol.com/...` |
| `/sil [URL]` | Remove product from tracking | `/sil https://www.trendyol.com/...` |
| `/listele` | List all tracked products | `/listele` |
| `/yenile` | Manual refresh - Check all product prices instantly | `/yenile` |
| `/threshold [%]` | Set price change notification threshold | `/threshold 10` |

### Adding Products

**Method 1: Command**
```
/ekle https://www.trendyol.com/product-link
```

**Method 2: Direct Link**
Simply paste any Trendyol link in the group:
```
https://www.trendyol.com/your-product-link
https://ty.gl/shortened-link
```

### Product List Features

The `/listele` command shows:
- 📈 **Price increased** from initial price
- 📉 **Price decreased** from initial price  
- ➡️ **No change** in price
- Direct links to products
- Current vs initial price comparison

### Manual Price Check

Use `/yenile` command to instantly check all tracked product prices:
- 🔄 **Instant Check**: Immediately checks all products without waiting for scheduled interval
- 📊 **Summary Report**: Shows how many products were checked and how many prices changed
- 🔔 **Immediate Notifications**: Sends instant notifications for any price changes found
- ⚡ **Safe Operation**: Uses the same functions as automatic checking, no system conflicts

### Price Change Threshold Configuration

Control when you get notified with `/threshold` command:
- 📊 **Custom Threshold**: Set different thresholds for each chat/group
- 🎯 **Percentage-Based**: Configure threshold as percentage (e.g., 5% = only notify if price changes by more than 5%)
- 📉 **Reduce Noise**: Avoid notifications for minor price fluctuations
- 💾 **Persistent**: Threshold is saved and remembered for your chat
- 📝 **View Current**: Use `/threshold` without parameters to see current setting

**Example Usage:**
```
/threshold 10      # Only notify if price changes by more than 10%
/threshold 0       # Get notified on any price change
/threshold         # View current threshold
```

### Sold-Out Product Tracking

The bot automatically detects and tracks product availability:
- 🚫 **Out-of-Stock Detection**: Automatically detects when products become unavailable
- 📱 **Sold-Out Notifications**: Get notified immediately when tracked products go out of stock
- 🟢 **Back-in-Stock Alerts**: Receive notification when sold-out products become available again
- 💾 **State Preservation**: Product tracking continues even when out of stock
- 🔄 **Automatic Updates**: Monitors stock status during every price check

**What Happens:**
1. Product goes out of stock → You get a "Product Sold Out" notification
2. Bot continues monitoring the product
3. Product comes back in stock → You get a "Back in Stock" notification with new price

## 🔄 How It Works

1. **Product Addition**: Bot scrapes product name and current price using multiple fallback methods
2. **Data Storage**: Information saved in `tracked_products.json` with initial and current prices
3. **Scheduled Checks**: Bot checks prices every X minutes (configurable via CHECK_INTERVAL)
4. **Manual Checks**: Use `/yenile` command for instant price checking
5. **Smart Notifications**: Only sends alerts when prices change beyond configured threshold
6. **Price Updates**: Database automatically updates with new prices
7. **Stock Monitoring**: Continuously monitors product availability and sends stock status alerts
8. **Error Handling**: Automatic retry with exponential backoff on network failures
9. **Admin Alerts**: Critical errors and high error rates trigger admin notifications

## 🐧 Automatic Startup (Linux/Raspberry Pi)

Create a systemd service for automatic startup:

```bash
sudo nano /etc/systemd/system/trendyol-bot.service
```

**Service configuration** (adjust paths for your setup):

```ini
[Unit]
Description=Trendyol Price Tracking Bot
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/telegram-trendyol-bot
ExecStart=/home/pi/telegram-trendyol-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable trendyol-bot.service
sudo systemctl start trendyol-bot.service
```

**Check status:**
```bash
sudo systemctl status trendyol-bot.service
```

## 📁 Project Structure

```
telegram-trendyol-bot/
├── main.py              # 🤖 Main bot logic and Telegram handlers
├── scraper.py           # 🕷️ Trendyol web scraping functionality
├── data_manager.py      # 💾 JSON data management (CRUD operations)
├── config.py           # ⚙️ Configuration and environment variables
├── requirements.txt    # 📦 Python dependencies
├── .env.example       # 📋 Environment variables template
├── .env              # 🔐 Your actual environment variables (create this)
├── tracked_products.json # 🗃️ Product database (auto-generated with bot)
└── README.md         # 📖 This documentation
```

### 🔧 Core Components

| File | Purpose | Key Functions |
|------|---------|---------------|
| `main.py` | Bot orchestration | Command handlers, price checking, notifications |
| `scraper.py` | Web scraping | Product info extraction, price parsing |
| `data_manager.py` | Data persistence | Add/remove products, price updates |
| `config.py` | Configuration | Environment variables, settings |

## 🔍 Technical Details

### Dependencies
- **python-telegram-bot 13.15**: Telegram Bot API wrapper
- **requests 2.31.0**: HTTP requests for web scraping
- **beautifulsoup4 4.12.2**: HTML parsing
- **lxml 4.9.3**: Fast XML/HTML parser
- **schedule 1.2.0**: Job scheduling
- **python-dotenv 1.0.0**: Environment variable management

### Key Features Implementation
- **Advanced Price Detection**: 7 different fallback methods for robust price extraction:
  1. New Trendyol structure with data-testid attributes
  2. price-price class search
  3. Legacy campaign-price and prc-dsc classes
  4. JSON-LD structured data extraction
  5. JavaScript variable parsing (winnerVariant, productDetail)
  6. General TL/₺ symbol search
  7. Multiple price container strategies
- **Intelligent Stock Detection**: Multiple methods for accurate stock status:
  - Add-to-cart button presence and text analysis
  - Buy-now button detection
  - Disabled button state checking
  - Out-of-stock message scanning
- **URL Validation**: Supports trendyol.com, ty.gl, tyml.gl, and trendyol-milla.com
- **Retry Strategy**: HTTP requests with exponential backoff (max 3 retries)
- **Anti-Bot Protection**: 
  - Random delays (1-3 seconds) between requests
  - Realistic user-agent headers
  - Session-based connection pooling
- **Error Recovery**: Comprehensive error handling with categorization and logging
- **Memory Efficient**: Minimal resource usage, ideal for 24/7 operation on Raspberry Pi
- **Thread Safety**: Proper threading for scheduler and bot operations
- **Admin Monitoring**: Automatic error notifications with diagnostic information

## 🐛 Troubleshooting

### Common Issues

**Bot not responding:**
- Check if `TELEGRAM_BOT_TOKEN` is correct
- Verify group ID is in `ALLOWED_GROUP_IDS`
- Ensure bot has proper permissions in the group

**Price not detected:**
- Trendyol may have changed their HTML structure
- Bot uses 7 different detection methods - if all fail, site structure changed significantly
- Check logs for scraping errors
- Try with different products
- Consider updating the scraper.py with new selectors

**Duplicate notifications:**
- Fixed with improved scheduler management
- Restart the bot if still occurring

**Memory issues on Raspberry Pi:**
- Reduce `CHECK_INTERVAL` to check less frequently
- Consider using swap if needed

### Logs and Debugging

Bot logs important events. Check console output for:
- Product addition/removal confirmations
- Price check results with detailed scraping attempts
- Error details with categorization (Network, Timeout, Connection, etc.)
- Notification sending status
- Stock status changes (sold-out, back-in-stock)
- Retry attempts and backoff delays
- HTTP request/response information
- Threshold updates and trigger events

**Debug Levels:**
- `INFO`: Normal operations (price checks, notifications sent)
- `WARNING`: Recoverable issues (retries, minor errors)
- `ERROR`: Serious problems (scraping failures, notification errors)
- `DEBUG`: Detailed technical information (HTML parsing, price extraction)

## ⚠️ Important Notes

- **Personal Use**: This bot is designed for personal/small group use
- **Rate Limiting**: Trendyol may implement anti-bot measures
- **Legal Compliance**: Ensure compliance with Trendyol's terms of service
- **Reliability**: While robust, web scraping can break if sites change structure
- **Privacy**: All data is stored locally in JSON format

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for:
- Bug fixes
- New features
- Documentation improvements
- Performance optimizations

## 🔗 Links

- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [BotFather](https://t.me/botfather) - Create your bot token
- [Trendyol](https://www.trendyol.com) - Supported e-commerce platform

---

# [TR] Trendyol Fiyat Takip Botu

Trendyol'daki ürün fiyatlarını takip eden ve fiyat değişikliklerinde akıllı bildirimler gönderen gelişmiş Telegram botu. Verimlilik ve güvenilirlik odaklı, geliştirilmiş kullanıcı deneyimi ile tasarlanmıştır.

## ✨ Özellikler

### Temel Özellikler
- 🔗 **Evrensel Link Desteği**: Trendyol.com, ty.gl (kısaltılmış), tyml.gl ve trendyol-milla.com linkleriyle çalışır
- ➕ **Kolay Ürün Ekleme**: `/ekle` komutu kullanın veya direkt Trendyol linki gönderin-paylaşın
- ➖ **Ürün Yönetimi**: `/sil` komutu ile ürünleri kaldırın
- 📋 **Akıllı Listeleme**: `/listele` ile fiyat trendleriyle birlikte tüm takip edilen ürünleri görün
- 🔄 **Otomatik Fiyat İzleme**: Yapılandırılabilir aralıklarla fiyat kontrolü
- 🎯 **Akıllı Bildirimler**: 
  - 📈 Kırmızı gösterge ile "Fiyat Yükseldi" bildirimleri
  - 📉 Yeşil gösterge ile "Fiyat Düştü" bildirimleri
  - Detaylı fiyat farkı ve yüzde değişim bilgisi
  - 🔔 Her sohbet için özelleştirilebilir bildirim eşiği
- 🔄 **Manuel Yenileme**: `/yenile` komutu ile tüm ürün fiyatlarını anında kontrol edin

### Gelişmiş Özellikler
- 🛒 **Tükenen Ürün Takibi**: 
  - Stokta olmayan ürünlerin otomatik tespiti
  - Ürünler tükendiğinde özel bildirimler
  - Ürünler tekrar stokta olduğunda geri geldi uyarıları
- ⚙️ **Dinamik Fiyat Eşiği**: 
  - `/threshold` komutu ile her sohbet için özel fiyat değişim eşiği belirleyin
  - Sadece eşiği aşan fiyat değişikliklerinde bildirim alın
  - Küçük fiyat dalgalanmalarında bildirim spamını önleyin
- 🏠 **Çoklu Grup Desteği**: Bot erişimini belirli Telegram gruplarıyla sınırlayın
- 🚨 **Gelişmiş Hata Yönetimi ve İzleme**:
  - Kritik hatalar için otomatik admin bildirimleri
  - Önerilen çözümlerle kategorize edilmiş hata mesajları
  - Yüksek hata oranı tespiti ve uyarıları
  - Hata ayıklama için detaylı loglama
- ⚡ **Optimize Edilmiş Performans**: Raspberry Pi ve düşük güçlü cihazlar için mükemmel hafif kod
- 🎨 **Zengin Formatlama**: Tıklanabilir linklerle HTML formatlı mesajlar

### Anti-Bot ve Güvenilirlik Özellikleri
- 🔄 **Akıllı Yeniden Deneme Stratejisi**: Hatalarda üstel geri çekilme ile otomatik yeniden deneme
- ⏱️ **Rastgele İstek Gecikmeleri**: İstekler arasında rastgele gecikmelerle anti-bot koruması
- 🔌 **Bağlantı Havuzu**: Bağlantı yeniden kullanımı ile verimli HTTP oturum yönetimi
- 🎯 **Çoklu Kazıma Yöntemleri**: Fiyat tespiti için 7 farklı yedek yöntem
- 📊 **JSON-LD Desteği**: Mevcut olduğunda yapılandırılmış verilerden fiyat çıkarımı
- 🧩 **JavaScript Ayrıştırma**: Gerektiğinde JavaScript değişkenlerinden fiyat çıkarabilir

## 📋 Gereksinimler

- **Python 3.6+** (Önerilen: Python 3.8 veya daha yeni)
- **pip** (Python paket yöneticisi)
- **Telegram Bot Token** ([@BotFather](https://t.me/botfather) üzerinden alınabilir)
- **Telegram Grup ID(leri)** erişim kontrolü için

## 🚀 Kurulum

### Hızlı Kurulum

1. **Repoyu klonlayın:**
```bash
git clone https://github.com/furkandlkdr/telegram-trendyol-bot.git
cd telegram-trendyol-bot
```

2. **Sanal ortam oluşturun ve etkinleştirin:**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. **Bağımlılıkları yükleyin:**
```bash
pip install -r requirements.txt
```

4. **Çevre değişkenlerini yapılandırın:**
   - `.env.example` dosyasını `.env` olarak kopyalayın
   - `.env` dosyasını ayarlarınızla düzenleyin:

```env
# @BotFather'dan alınan Telegram Bot Token
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Dakika cinsinden fiyat kontrol aralığı (varsayılan: 30)
CHECK_INTERVAL=30

# İzin verilen Telegram grup ID'lerinin virgülle ayrılmış listesi
ALLOWED_GROUP_IDS=-1001234567890,-1009876543210
```

5. **Botu başlatın:**
```bash
python main.py
```

## 🔧 Grup ID'si Alma

Telegram grup ID'nizi bulmak için:

1. Botu grubunuza ekleyin
2. Grupta herhangi bir mesaj gönderin
3. Şu adresi ziyaret edin: `https://api.telegram.org/bot{BOT_TOKEN_INIIZ}/getUpdates`
4. JSON yanıtında `"chat":{"id": -1001234567890}` bölümünü arayın
5. Negatif sayıyı (eksi işaretiyle birlikte) kopyalayın

## 📖 Kullanım Kılavuzu

### Temel Komutlar

| Komut | Açıklama | Örnek |
|-------|----------|-------|
| `/start` | Botu başlat ve yardımı göster | `/start` |
| `/ekle [URL]` | Ürünü takibe ekle | `/ekle https://www.trendyol.com/...` |
| `/sil [URL]` | Ürünü takipten çıkar | `/sil https://www.trendyol.com/...` |
| `/listele` | Tüm takip edilen ürünleri listele | `/listele` |
| `/yenile` | Manuel yenileme - Tüm ürün fiyatlarını anında kontrol et | `/yenile` |
| `/threshold [%]` | Fiyat değişim bildirim eşiğini ayarla | `/threshold 10` |

### Ürün Ekleme

**Yöntem 1: Komut**
```
/ekle https://www.trendyol.com/urun-linki
```

**Yöntem 2: Direkt Link**
Herhangi bir Trendyol linkini gruba yapıştırın:
```
https://www.trendyol.com/urun-linkiniz
https://ty.gl/kisaltilmis-link
```

### Ürün Listesi Özellikleri

`/listele` komutu şunları gösterir:
- 📈 **Başlangıç fiyatından artış**
- 📉 **Başlangıç fiyatından düşüş**  
- ➡️ **Fiyatta değişiklik yok**
- Ürünlere direkt linkler
- Güncel ve başlangıç fiyat karşılaştırması

### Manuel Fiyat Kontrolü

`/yenile` komutu ile tüm takip edilen ürün fiyatlarını anında kontrol edin:
- 🔄 **Anında Kontrol**: Zamanlanmış aralığı beklemeden tüm ürünleri hemen kontrol eder
- 📊 **Özet Rapor**: Kaç ürün kontrol edildiğini ve kaç tanesinde fiyat değiştiğini gösterir
- 🔔 **Anında Bildirimler**: Bulunan fiyat değişiklikleri için anında bildirim gönderir
- ⚡ **Güvenli İşlem**: Otomatik kontrolle aynı fonksiyonları kullanır, sistem çakışması yaşanmaz

### Fiyat Değişim Eşiği Yapılandırması

`/threshold` komutu ile ne zaman bildirim alacağınızı kontrol edin:
- 📊 **Özel Eşik**: Her sohbet/grup için farklı eşikler belirleyin
- 🎯 **Yüzde Tabanlı**: Eşiği yüzde olarak yapılandırın (örn: %5 = sadece fiyat %5'ten fazla değişirse bildir)
- 📉 **Gürültüyü Azalt**: Küçük fiyat dalgalanmaları için bildirim almayın
- 💾 **Kalıcı**: Eşik kaydedilir ve sohbetiniz için hatırlanır
- 📝 **Mevcut Değeri Gör**: Parametresiz `/threshold` kullanarak mevcut ayarı görün

**Kullanım Örnekleri:**
```
/threshold 10      # Sadece fiyat %10'dan fazla değişirse bildir
/threshold 0       # Her fiyat değişikliğinde bildir
/threshold         # Mevcut eşiği görüntüle
```

### Tükenen Ürün Takibi

Bot otomatik olarak ürün bulunabilirliğini tespit eder ve takip eder:
- 🚫 **Stokta Yok Tespiti**: Ürünler stokta kalmadığında otomatik tespit
- 📱 **Tükendi Bildirimleri**: Takip edilen ürünler tükendiğinde anında bildirim
- 🟢 **Stokta Geri Geldi Uyarıları**: Tükenen ürünler tekrar satışa çıktığında bildirim
- 💾 **Durum Koruma**: Ürün takibi stokta olmasa bile devam eder
- 🔄 **Otomatik Güncellemeler**: Her fiyat kontrolünde stok durumunu izler

**Nasıl Çalışır:**
1. Ürün stoktan tükenir → "Ürün Tükendi" bildirimi alırsınız
2. Bot ürünü izlemeye devam eder
3. Ürün tekrar stokta olur → Yeni fiyatıyla "Stokta Geri Geldi" bildirimi alırsınız

## 🔄 Nasıl Çalışır

1. **Ürün Ekleme**: Bot çoklu yedek yöntemler kullanarak ürün adını ve güncel fiyatı çeker
2. **Veri Saklama**: Bilgiler `tracked_products.json` dosyasında başlangıç ve güncel fiyatlarla saklanır
3. **Zamanlanmış Kontroller**: Bot her X dakikada bir fiyatları kontrol eder (CHECK_INTERVAL ile yapılandırılabilir)
4. **Manuel Kontroller**: `/yenile` komutu ile anında fiyat kontrolü yapın
5. **Akıllı Bildirimler**: Sadece fiyatlar yapılandırılan eşiğin üzerinde değiştiğinde uyarı gönderir
6. **Fiyat Güncellemeleri**: Veritabanı otomatik olarak yeni fiyatlarla güncellenir
7. **Stok İzleme**: Ürün bulunabilirliğini sürekli izler ve stok durumu uyarıları gönderir
8. **Hata Yönetimi**: Ağ hatalarında üstel geri çekilme ile otomatik yeniden deneme
9. **Admin Uyarıları**: Kritik hatalar ve yüksek hata oranları admin bildirimlerini tetikler

## 🐧 Otomatik Başlatma (Linux/Raspberry Pi)

Otomatik başlatma için systemd servisi oluşturun:

```bash
sudo nano /etc/systemd/system/trendyol-bot.service
```

**Servis yapılandırması** (yolları kendi kurulumunuza göre ayarlayın):

```ini
[Unit]
Description=Trendyol Fiyat Takip Botu
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/telegram-trendyol-bot
ExecStart=/home/pi/telegram-trendyol-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Etkinleştirin ve başlatın:**
```bash
sudo systemctl enable trendyol-bot.service
sudo systemctl start trendyol-bot.service
```

**Durumu kontrol edin:**
```bash
sudo systemctl status trendyol-bot.service
```

## 📁 Proje Yapısı

```
telegram-trendyol-bot/
├── main.py              # 🤖 Ana bot mantığı ve Telegram işleyicileri
├── scraper.py           # 🕷️ Trendyol web kazıma işlevselliği
├── data_manager.py      # 💾 JSON veri yönetimi (CRUD işlemleri)
├── config.py           # ⚙️ Yapılandırma ve çevre değişkenleri
├── requirements.txt    # 📦 Python bağımlılıkları
├── .env.example       # 📋 Çevre değişkenleri şablonu
├── .env              # 🔐 Gerçek çevre değişkenleriniz (bunu oluşturun)
├── tracked_products.json # 🗃️ Ürün veritabanı (bot tarafından otomatik oluşturulur)
└── README.md         # 📖 Bu dokümantasyon
```

### 🔧 Temel Bileşenler

| Dosya | Amaç | Ana Fonksiyonlar |
|-------|------|------------------|
| `main.py` | Bot orkestras | Komut işleyicileri, fiyat kontrolü, bildirimler |
| `scraper.py` | Web kazıma | Ürün bilgisi çıkarma, fiyat ayrıştırma |
| `data_manager.py` | Veri kalıcılığı | Ürün ekleme/çıkarma, fiyat güncellemeleri |
| `config.py` | Yapılandırma | Çevre değişkenleri, ayarlar |

## 🔍 Teknik Detaylar

### Bağımlılıklar
- **python-telegram-bot 13.15**: Telegram Bot API sarmalayıcısı
- **requests 2.31.0**: Web kazıma için HTTP istekleri
- **beautifulsoup4 4.12.2**: HTML ayrıştırma
- **lxml 4.9.3**: Hızlı XML/HTML ayrıştırıcısı
- **schedule 1.2.0**: İş zamanlama
- **python-dotenv 1.0.0**: Çevre değişkeni yönetimi

### Ana Özellikler Uygulaması
- **Gelişmiş Fiyat Tespiti**: Sağlam fiyat çıkarma için 7 farklı yedek yöntem:
  1. Yeni Trendyol yapısı (data-testid özellikleri)
  2. price-price sınıf araması
  3. Eski campaign-price ve prc-dsc sınıfları
  4. JSON-LD yapılandırılmış veri çıkarımı
  5. JavaScript değişken ayrıştırma (winnerVariant, productDetail)
  6. Genel TL/₺ sembol araması
  7. Çoklu fiyat konteyner stratejileri
- **Akıllı Stok Tespiti**: Doğru stok durumu için çoklu yöntemler:
  - Sepete ekle butonu varlığı ve metin analizi
  - Hemen al butonu tespiti
  - Devre dışı buton durum kontrolü
  - Stokta yok mesaj taraması
- **URL Doğrulama**: trendyol.com, ty.gl, tyml.gl ve trendyol-milla.com destekler
- **Yeniden Deneme Stratejisi**: Üstel geri çekilme ile HTTP istekleri (maks 3 deneme)
- **Anti-Bot Koruması**: 
  - İstekler arası rastgele gecikmeler (1-3 saniye)
  - Gerçekçi kullanıcı-agent başlıkları
  - Oturum tabanlı bağlantı havuzu
- **Hata Kurtarma**: Kategorilendirme ve loglama ile kapsamlı hata yönetimi
- **Bellek Verimli**: Minimal kaynak kullanımı, Raspberry Pi'de 7/24 işletim için ideal
- **Thread Güvenliği**: Zamanlayıcı ve bot işlemleri için uygun threading
- **Admin İzleme**: Tanı bilgileri ile otomatik hata bildirimleri

## 🔬 Advanced Scraping Techniques

### Multi-Method Price Detection

The bot uses a sophisticated waterfall approach to extract prices, trying 7 different methods in order:

1. **Modern Trendyol Structure** (Primary)
   - Searches for `data-testid="price"` containers
   - Looks for discounted prices first, then original prices
   - Handles multiple price display formats

2. **Class-Based Search** (Secondary)
   - `price-price` class divs
   - `campaign-price` paragraphs
   - `prc-dsc` span elements

3. **Structured Data** (Tertiary)
   - Parses JSON-LD schema.org markup
   - Extracts from `offers.price` fields
   - Handles both single and array offers

4. **JavaScript Variables** (Quaternary)
   - Searches for `winnerVariant` object
   - Looks for `productDetail` data
   - Extracts from various price field names

5. **Symbol Search** (Last Resort)
   - General TL/₺ symbol search
   - Price range validation (0.01-100,000 TL)
   - Filters out IDs and non-price numbers

### Stock Status Detection

Multiple methods ensure accurate stock detection:

- **Button Analysis**: Checks add-to-cart and buy-now button presence and text
- **Disabled State**: Detects disabled purchase buttons
- **Text Scanning**: Searches for out-of-stock messages in visible elements
- **Context Filtering**: Ignores JavaScript code and metadata to avoid false positives

### Anti-Bot Features

- **Random Delays**: 1-3 second randomized delays between requests
- **Retry with Backoff**: Exponential backoff (2^attempt + random)
- **Session Pooling**: Reuses HTTP connections for efficiency
- **Realistic Headers**: Browser-like user agent and accept headers
- **Error Recovery**: Graceful degradation on failures

## 🔬 Gelişmiş Kazıma Teknikleri

### Çok Yöntemli Fiyat Tespiti

Bot fiyatları çıkarmak için sofistike bir şelale yaklaşımı kullanır, 7 farklı yöntemi sırayla dener:

1. **Modern Trendyol Yapısı** (Birincil)
   - `data-testid="price"` konteynerlerini arar
   - Önce indirimli fiyatlara, sonra orijinal fiyatlara bakar
   - Çoklu fiyat gösterim formatlarını işler

2. **Sınıf Tabanlı Arama** (İkincil)
   - `price-price` sınıf divleri
   - `campaign-price` paragrafları
   - `prc-dsc` span elementleri

3. **Yapılandırılmış Veri** (Üçüncül)
   - JSON-LD schema.org işaretlemesini ayrıştırır
   - `offers.price` alanlarından çıkarır
   - Hem tekli hem dizi tekliflerini işler

4. **JavaScript Değişkenleri** (Dörtüncül)
   - `winnerVariant` objesini arar
   - `productDetail` verisine bakar
   - Çeşitli fiyat alan adlarından çıkarır

5. **Sembol Araması** (Son Çare)
   - Genel TL/₺ sembol araması
   - Fiyat aralığı doğrulaması (0.01-100.000 TL)
   - ID'leri ve fiyat olmayan sayıları filtreler

### Stok Durumu Tespiti

Doğru stok tespiti için çoklu yöntemler:

- **Buton Analizi**: Sepete ekle ve hemen al butonlarının varlığını ve metnini kontrol eder
- **Devre Dışı Durum**: Devre dışı satın alma butonlarını tespit eder
- **Metin Tarama**: Görünür elementlerde stokta yok mesajlarını arar
- **Bağlam Filtreleme**: Yanlış pozitifleri önlemek için JavaScript kodu ve metadatayı yok sayar

### Anti-Bot Özellikleri

- **Rastgele Gecikmeler**: İstekler arası 1-3 saniye rastgele gecikmeler
- **Geri Çekilme ile Yeniden Deneme**: Üstel geri çekilme (2^deneme + rastgele)
- **Oturum Havuzu**: Verimlilik için HTTP bağlantılarını yeniden kullanır
- **Gerçekçi Başlıklar**: Tarayıcı benzeri kullanıcı aracı ve kabul başlıkları
- **Hata Kurtarma**: Hatalarda zarif düşüş

## 🐛 Sorun Giderme

### Yaygın Sorunlar

**Bot yanıt vermiyor:**
- `TELEGRAM_BOT_TOKEN`'ın doğru olduğunu kontrol edin
- Grup ID'sinin `ALLOWED_GROUP_IDS`'te olduğunu doğrulayın
- Botun grupta uygun izinlere sahip olduğundan emin olun

**Fiyat tespit edilmiyor:**
- Trendyol HTML yapısını değiştirmiş olabilir
- Bot 7 farklı tespit yöntemi kullanır - hepsi başarısız olursa site yapısı önemli ölçüde değişmiş
- Kazıma hatalarını kontrol etmek için logları inceleyin
- Farklı ürünlerle deneyin
- Yeni seçicilerle scraper.py'yi güncellemeyi düşünün

**Çift bildirim:**
- Geliştirilmiş zamanlayıcı yönetimiyle düzeltildi
- Hala oluşuyorsa botu yeniden başlatın

**Raspberry Pi'de bellek sorunları:**
- Daha az sıklıkta kontrol için `CHECK_INTERVAL`'ı artırın
- Gerekirse swap kullanmayı düşünün

### Loglar ve Hata Ayıklama

Bot önemli olayları loglar. Konsol çıktısında şunları kontrol edin:
- Ürün ekleme/çıkarma onayları
- Detaylı kazıma denemeleriyle fiyat kontrol sonuçları
- Kategorilendirme ile hata detayları (Ağ, Zaman Aşımı, Bağlantı, vb.)
- Bildirim gönderme durumu
- Stok durumu değişiklikleri (tükendi, stokta geri geldi)
- Yeniden deneme girişimleri ve geri çekilme gecikmeleri
- HTTP istek/yanıt bilgileri
- Eşik güncellemeleri ve tetikleme olayları

**Hata Seviyeleri:**
- `INFO`: Normal işlemler (fiyat kontrolleri, bildirim gönderildi)
- `WARNING`: Kurtarılabilir sorunlar (yeniden denemeler, küçük hatalar)
- `ERROR`: Ciddi problemler (kazıma hataları, bildirim hataları)
- `DEBUG`: Detaylı teknik bilgiler (HTML ayrıştırma, fiyat çıkarımı)

## ⚠️ Önemli Notlar

- **Kişisel Kullanım**: Bu bot kişisel/küçük grup kullanımı için tasarlanmıştır
- **Hız Sınırlaması**: Trendyol anti-bot önlemleri uygulayabilir
- **Yasal Uyumluluk**: Trendyol'un kullanım şartlarına uygunluğu sağlayın
- **Güvenilirlik**: Sağlam olmasına rağmen, siteler yapı değiştirirse web kazıma bozulabilir
- **Gizlilik**: Tüm veriler yerel olarak JSON formatında saklanır

## 🛡️ Hata İzleme ve Bildirimler

### Otomatik Hata Bildirimleri

Bot artık hataları otomatik olarak admin'e bildirir:

- 🚨 **Kritik Hatalar**: Bot çöktüğünde anında bildirim
- ⚠️ **Scraping Hataları**: Çok sayıda scraping hatası durumunda uyarı
- 📊 **Watchdog Raporları**: Bot durumu hakkında düzenli bilgiler

### Admin Chat ID Ayarlama

`.env` dosyanıza admin chat ID'nizi ekleyin:

```env
ADMIN_CHAT_ID=123456789
```

**Chat ID'nizi bulmak için:**
1. Bot'unuza `/start` mesajı gönderin
2. `https://api.telegram.org/bot{BOT_TOKEN}/getUpdates` adresini ziyaret edin
3. `"from":{"id": 123456789}` değerini kopyalayın

### Watchdog Sistemi

Watchdog scripti botunuzu sürekli izler:

- ✅ **Process İzleme**: Bot çalışıp çalışmadığını kontrol eder
- 🔄 **Otomatik Restart**: Bot durduğunda otomatik yeniden başlatır  
- 📱 **Telegram Bildirimleri**: Tüm olaylar için bildirim gönderir
- 📝 **Detaylı Loglama**: Tüm aktiviteler loglanır

## 🥧 Raspberry Pi Özel Kurulum

### Otomatik Kurulum

```bash
# Projeyi klonlayın
git clone https://github.com/furkandlkdr/telegram-trendyol-bot.git
cd telegram-trendyol-bot

# Kurulum scriptini çalıştırın
chmod +x install_raspberry.sh
./install_raspberry.sh
```

### Manuel Kurulum

**1. Sistem hazırlığı:**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl
```

**2. Proje kurulumu:**
```bash
git clone https://github.com/furkandlkdr/telegram-trendyol-bot.git
cd telegram-trendyol-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3. Çevre değişkenleri:**
```bash
cp .env.example .env
nano .env  # Ayarlarınızı girin
```

**4. Systemd servisleri:**
```bash
sudo cp systemd/trendyol-bot.service /etc/systemd/system/
sudo cp systemd/trendyol-watchdog.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable trendyol-bot.service
sudo systemctl enable trendyol-watchdog.service
```

**5. Servisleri başlatın:**
```bash
sudo systemctl start trendyol-bot.service
sudo systemctl start trendyol-watchdog.service
```

### Raspberry Pi İzleme Komutları

**Servis durumu:**
```bash
sudo systemctl status trendyol-bot.service
sudo systemctl status trendyol-watchdog.service
```

**Canlı loglar:**
```bash
sudo journalctl -u trendyol-bot.service -f
sudo journalctl -u trendyol-watchdog.service -f
```

**Servis yönetimi:**
```bash
sudo systemctl restart trendyol-bot.service
sudo systemctl stop trendyol-bot.service
sudo systemctl start trendyol-bot.service
```

**Sistem kaynaklarını izleme:**
```bash
htop                    # CPU ve RAM kullanımı
df -h                   # Disk kullanımı
free -h                 # Bellek durumu
journalctl --disk-usage # Log disk kullanımı
```

### Performans Optimizasyonları

**Bellek optimizasyonu:**
```bash
# Swap dosyası oluştur (isteğe bağlı)
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# /etc/fstab'a ekle
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**Log döngüsü:**
```bash
# Log boyutunu sınırla
sudo nano /etc/systemd/journald.conf
# Şu satırları uncomment edin:
# SystemMaxUse=50M
# MaxRetentionSec=1week

sudo systemctl restart systemd-journald
```

### Sorun Giderme

**Bot başlamıyor:**
```bash
# Detaylı log kontrol
sudo journalctl -u trendyol-bot.service --no-pager

# Manuel test
cd /home/pi/telegram-trendyol-bot
source venv/bin/activate
python main.py
```

**Watchdog çalışmıyor:**
```bash
# Process kontrolü
ps aux | grep python
ps aux | grep watchdog

# Manuel watchdog testi
cd /home/pi/telegram-trendyol-bot
source venv/bin/activate
python watchdog.py
```

**Bellek sorunu:**
```bash
# Bellek kullanımını kontrol et
free -h
sudo systemctl status

# Gereksiz servisleri durdur
sudo systemctl disable bluetooth.service
sudo systemctl disable hciuart.service
```

## 🤝 Katkıda Bulunma

Katkılar memnuniyetle karşılanır! Lütfen şunlar için pull request gönderin veya issue açın:
- Hata düzeltmeleri
- Yeni özellikler
- Dokümantasyon iyileştirmeleri
- Performans optimizasyonları

## 📄 Lisans

Bu proje açık kaynaklıdır ve MIT Lisansı altında mevcuttur.

## 🔗 Linkler

- [Telegram Bot API Dokümantasyonu](https://core.telegram.org/bots/api)
- [BotFather](https://t.me/botfather) - Bot token'ınızı oluşturun
- [Trendyol](https://www.trendyol.com) - Desteklenen e-ticaret platformu
