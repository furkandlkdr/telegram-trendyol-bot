#!/usr/bin/env python3
"""
Trendyol Bot Watchdog Script
Bu script botun çalışıp çalışmadığını kontrol eder ve çöktüğünde admin'e bildirir.
"""

import psutil
import time
import requests
import subprocess
import logging
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('watchdog.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Watchdog ayarları
PROCESS_NAME = "python"
SCRIPT_NAME = "main.py"
CHECK_INTERVAL = 300  # 5 dakika
MAX_RESTART_ATTEMPTS = 3
RESTART_DELAY = 30  # 30 saniye

class TrendyolBotWatchdog:
    def __init__(self):
        self.restart_attempts = 0
        self.last_restart_time = 0
        
    def send_telegram_message(self, message):
        """Telegram mesajı gönder"""
        if not TELEGRAM_BOT_TOKEN or not ADMIN_CHAT_ID:
            logger.warning("Bot token veya admin chat ID eksik. Telegram bildirimi gönderilemedi.")
            return False
            
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {
                'chat_id': ADMIN_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info("Telegram bildirimi başarıyla gönderildi")
                return True
            else:
                logger.error(f"Telegram API hatası: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Telegram mesaj gönderilemedi: {e}")
            return False

    def is_bot_running(self):
        """Bot'un çalışıp çalışmadığını kontrol et"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == PROCESS_NAME:
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if SCRIPT_NAME in cmdline and 'watchdog.py' not in cmdline:
                        logger.debug(f"Bot process bulundu: PID {proc.info['pid']}")
                        return True, proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return False, None

    def restart_bot(self):
        """Bot'u yeniden başlat"""
        current_time = time.time()
        
        # Çok sık restart yapmayı önle
        if current_time - self.last_restart_time < 60:
            logger.warning("Son restart'tan 1 dakika geçmedi, bekleniyor...")
            return False
            
        self.last_restart_time = current_time
        self.restart_attempts += 1
        
        if self.restart_attempts > MAX_RESTART_ATTEMPTS:
            logger.error(f"Maksimum restart denemesi ({MAX_RESTART_ATTEMPTS}) aşıldı")
            return False
            
        try:
            # Systemd service kullanıyorsanız
            logger.info("Systemd service ile bot yeniden başlatılıyor...")
            result = subprocess.run(
                ['sudo', 'systemctl', 'restart', 'trendyol-bot.service'], 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info("Systemd service başarıyla yeniden başlatıldı")
                time.sleep(RESTART_DELAY)
                return True
            else:
                logger.error(f"Systemd restart hatası: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("Systemd restart zaman aşımına uğradı")
        except subprocess.CalledProcessError as e:
            logger.error(f"Systemd komutu başarısız: {e}")
        except Exception as e:
            logger.error(f"Systemd restart hatası: {e}")
        
        # Manuel fallback kaldırıldı: systemd Restart=always zaten devrede.
        # Ayrı bir Popen ile ikinci instance başlatmak getUpdates Conflict'e yol açıyordu.
        logger.error("Systemd restart başarısız. systemd'in Restart=always politikasına bırakılıyor; manuel ikinci instance başlatılmayacak.")
        return False

    def reset_restart_counter(self):
        """Restart sayacını sıfırla"""
        if self.restart_attempts > 0:
            logger.info("Bot başarıyla çalışıyor, restart sayacı sıfırlandı")
            self.restart_attempts = 0

    def run(self):
        """Ana watchdog döngüsü"""
        logger.info("Trendyol Bot Watchdog başlatıldı")
        
        # Başlangıç bildirimi
        self.send_telegram_message(
            f"🤖 <b>Trendyol Bot Watchdog Başlatıldı</b>\n\n"
            f"<b>Zaman:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"<b>Kontrol Aralığı:</b> {CHECK_INTERVAL // 60} dakika\n"
            f"<b>Durum:</b> İzleme aktif"
        )
        
        consecutive_failures = 0
        
        while True:
            try:
                is_running, pid = self.is_bot_running()
                
                if is_running:
                    logger.debug(f"Bot çalışıyor (PID: {pid})")
                    self.reset_restart_counter()
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    logger.error(f"Bot çalışmıyor! (Ardışık hata: {consecutive_failures})")
                    
                    # İlk hatada hemen bildir ve restart dene
                    if consecutive_failures == 1:
                        message = f"""
🚨 <b>Trendyol Bot Durdu!</b>

<b>Zaman:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
<b>Durum:</b> Process bulunamadı
<b>Restart Denemesi:</b> {self.restart_attempts + 1}/{MAX_RESTART_ATTEMPTS}

Yeniden başlatılıyor...
                        """
                        self.send_telegram_message(message)
                        
                        if self.restart_bot():
                            # Restart sonrası kontrol et
                            time.sleep(10)
                            is_running_after_restart, new_pid = self.is_bot_running()
                            
                            if is_running_after_restart:
                                success_message = f"""
✅ <b>Bot Başarıyla Yeniden Başlatıldı!</b>

<b>Zaman:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
<b>Yeni PID:</b> {new_pid}
<b>Restart Denemesi:</b> {self.restart_attempts}/{MAX_RESTART_ATTEMPTS}
                                """
                                self.send_telegram_message(success_message)
                                consecutive_failures = 0
                            else:
                                error_message = f"""
❌ <b>Bot Yeniden Başlatılamadı!</b>

<b>Zaman:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
<b>Restart Denemesi:</b> {self.restart_attempts}/{MAX_RESTART_ATTEMPTS}

{'Manuel müdahale gerekli!' if self.restart_attempts >= MAX_RESTART_ATTEMPTS else 'Tekrar denenecek...'}
                                """
                                self.send_telegram_message(error_message)
                        else:
                            error_message = f"""
❌ <b>Bot Restart Başarısız!</b>

<b>Zaman:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
<b>Restart Denemesi:</b> {self.restart_attempts}/{MAX_RESTART_ATTEMPTS}

Logları kontrol edin. Manuel müdahale gerekebilir.
                            """
                            self.send_telegram_message(error_message)
                
                # Kontrol aralığı bekle
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("Watchdog durduruldu (Ctrl+C)")
                self.send_telegram_message(
                    f"🛑 <b>Watchdog Durduruldu</b>\n\n"
                    f"<b>Zaman:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
                    f"<b>Sebep:</b> Manuel durdurma"
                )
                break
                
            except Exception as e:
                logger.error(f"Watchdog hatası: {e}")
                time.sleep(60)  # Hata durumunda 1 dakika bekle

if __name__ == "__main__":
    watchdog = TrendyolBotWatchdog()
    watchdog.run()
