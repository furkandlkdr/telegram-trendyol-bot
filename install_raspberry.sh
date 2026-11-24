#!/bin/bash
# Trendyol Bot Raspberry Pi Kurulum Scripti

set -e  # Hata durumunda durdur

# Renkler
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log fonksiyonu
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Root kontrolü
if [[ $EUID -eq 0 ]]; then
   error "Bu script root olarak çalıştırılmamalıdır!"
   exit 1
fi

log "🚀 Trendyol Bot Raspberry Pi Kurulumu Başlıyor..."

# Sistem güncellemesi
log "📦 Sistem paketleri güncelleniyor..."
sudo apt update && sudo apt upgrade -y

# Gerekli paketleri yükle
log "🔧 Gerekli paketler yükleniyor..."
sudo apt install -y python3 python3-pip python3-venv git curl bc

# Python sürümünü kontrol et
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
log "🐍 Python sürümü: $PYTHON_VERSION"

# Python sürüm kontrolü (bc olmadan)
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 6 ]); then
    error "Python 3.6 veya daha yeni sürüm gerekli! Mevcut sürüm: $PYTHON_VERSION"
    exit 1
else
    log "✅ Python sürümü uygun: $PYTHON_VERSION"
fi

# Proje dizinine git
CURRENT_USER=$(whoami)
PROJECT_DIR="/home/$CURRENT_USER/telegram-trendyol-bot"
if [ ! -d "$PROJECT_DIR" ]; then
    error "Proje dizini bulunamadı: $PROJECT_DIR"
    error "Önce projeyi bu dizine klonlayın: git clone <repo_url> $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"
log "📂 Proje dizini: $PROJECT_DIR"

# Virtual environment oluştur
log "🌐 Virtual environment oluşturuluyor..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Virtual environment'ı aktifleştir
source venv/bin/activate

# Paketleri yükle
log "📦 Python paketleri yükleniyor..."
pip install --upgrade pip
pip install -r requirements.txt

# .env dosyası kontrolü
if [ ! -f ".env" ]; then
    warning ".env dosyası bulunamadı!"
    log "📝 .env.example dosyasından .env oluşturuluyor..."
    cp .env.example .env
    
    echo ""
    warning "⚠️  ÖNEMLİ: .env dosyasını düzenlemeniz gerekiyor!"
    echo ""
    echo "nano .env komutu ile aşağıdaki değerleri doldurun:"
    echo "- TELEGRAM_BOT_TOKEN: Bot token'ınız"
    echo "- ALLOWED_GROUP_IDS: İzin verilen grup ID'leri"
    echo "- ADMIN_CHAT_ID: Hata bildirimleri için chat ID'niz"
    echo ""
    read -p "Devam etmek için Enter'e basın..."
fi

# Dosya izinlerini ayarla
log "🔒 Dosya izinleri ayarlanıyor..."
chmod +x watchdog.py
chmod +x install_raspberry.sh

# Systemd servislerini kopyala
log "⚙️ Systemd servisleri yapılandırılıyor..."

# Servis dosyalarını kopyala
sudo cp systemd/trendyol-bot.service /etc/systemd/system/
sudo cp systemd/trendyol-watchdog.service /etc/systemd/system/

# Systemd'yi yeniden yükle
sudo systemctl daemon-reload

# Servisleri etkinleştir (henüz başlatma)
sudo systemctl enable trendyol-bot.service
sudo systemctl enable trendyol-watchdog.service

log "✅ Kurulum tamamlandı!"

echo ""
echo "==================== SONRAKI ADIMLAR ===================="
echo ""
info "1. .env dosyasını düzenleyin:"
echo "   nano .env"
echo ""
info "2. Bot'u test edin:"
echo "   cd $PROJECT_DIR"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
info "3. Test başarılıysa servisleri başlatın:"
echo "   sudo systemctl start trendyol-bot.service"
echo "   sudo systemctl start trendyol-watchdog.service"
echo ""
info "4. Servis durumunu kontrol edin:"
echo "   sudo systemctl status trendyol-bot.service"
echo "   sudo systemctl status trendyol-watchdog.service"
echo ""
info "5. Logları görüntüleyin:"
echo "   sudo journalctl -u trendyol-bot.service -f"
echo "   sudo journalctl -u trendyol-watchdog.service -f"
echo ""
warning "⚠️  .env dosyasını düzenlemeyi unutmayın!"
echo "========================================================"
