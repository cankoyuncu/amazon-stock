import requests
from bs4 import BeautifulSoup
import time
import telegram
import logging
import os
from datetime import datetime

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_monitor.log'),
        logging.StreamHandler()
    ]
)

# Telegram ayarları - ortam değişkenlerinden al
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

if not bot_token or not chat_id:
    logging.error("TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID ortam değişkenleri gerekli!")
    exit(1)

bot = telegram.Bot(token=bot_token)

# Amazon Wishlist URL'si
wishlist_url = "https://www.amazon.com.tr/hz/wishlist/ls/PA6IQDW9HR53"

# CSS Selector
product_selector = "#pab-I3GQCIP0S7X0C7 > span > a"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# Son durum takibi
last_status = None

def check_wishlist_stock():
    global last_status
    
    try:
        logging.info("Wishlist kontrol ediliyor...")
        response = requests.get(wishlist_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Belirtilen CSS selector ile elementi bul
        product_element = soup.select_one(product_selector)
        
        if product_element:
            button_text = product_element.get_text(strip=True)
            logging.info(f"Bulunan metin: '{button_text}'")
            
            if "Sepete Ekle" in button_text:
                current_status = "in_stock"
                if current_status != last_status:
                    try:
                        # Telegram mesajı gönder
                        message = f"🟢 STOK UYARISI!\n\n"
                        message += f"Ürün stokta! 'Sepete Ekle' butonu aktif.\n\n"
                        message += f"Wishlist: {wishlist_url}\n\n"
                        message += f"Zaman: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        
                        bot.send_message(chat_id=chat_id, text=message)
                        logging.info("✅ Stok bildirim mesajı gönderildi!")
                        last_status = current_status
                    except Exception as telegram_error:
                        logging.error(f"Telegram mesaj gönderme hatası: {telegram_error}")
                else:
                    logging.info("Ürün hala stokta - Bildirim daha önce gönderildi")
                    
            elif "Satın alma seçeneklerini gör" in button_text:
                current_status = "out_of_stock"
                if current_status != last_status:
                    logging.info("❌ Ürün stokta değil - 'Satın alma seçeneklerini gör' durumunda")
                    last_status = current_status
                else:
                    logging.info("Ürün hala stokta değil")
            else:
                logging.warning(f"Beklenmeyen metin bulundu: '{button_text}'")
        else:
            logging.error(f"Element bulunamadı! CSS Selector: {product_selector}")
            logging.info("Sayfa yapısı değişmiş olabilir, kontrol edin.")
            
    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP Hatası: {e}")
    except Exception as e:
        logging.error(f"Genel hata: {e}")

def main():
    logging.info("Amazon Wishlist stok takip botu başlatıldı")
    logging.info(f"İzlenen Wishlist: {wishlist_url}")
    logging.info(f"CSS Selector: {product_selector}")
    
    while True:
        try:
            check_wishlist_stock()
            time.sleep(60)  # 1 dakika bekle
            
        except KeyboardInterrupt:
            logging.info("🛑 Bot kullanıcı tarafından durduruldu")
            break
        except Exception as e:
            logging.error(f"Ana döngü hatası: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()