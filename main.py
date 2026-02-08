import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import datetime
import os
import sys
import time

# ==========================================
# KONFIGURASI SUPER AGENT
# ==========================================

# 1. SETUP KUNCI RAHASIA (Otomatis ambil dari GitHub Secrets)
TOKEN = os.environ.get("TOKEN_TELEGRAM")
ID_TUJUAN = os.environ.get("CHAT_ID")

# Fallback jika dijalankan di Laptop (Isi manual jika mau tes lokal)
if not TOKEN: TOKEN = "ISI_TOKEN_DISINI_JIKA_TES_LOKAL"
if not ID_TUJUAN: ID_TUJUAN = "ISI_ID_DISINI_JIKA_TES_LOKAL"

# 2. DAFTAR KOIN UTAMA (Untuk Pantau Harga & Sentimen)
COINS = [
    "bitcoin", "ethereum", "solana", "binancecoin", "ripple", 
    "dogecoin", "shiba-inu", "pepe", "floki", "bonk",
    "sui", "sei", "aptos", "render-token", "fetch-ai",
    "avalanche-2", "fantom", "optimism", "arbitrum"
]

# 3. MAPPING (Nama di Berita -> ID di CoinGecko)
# Agar bot tau kalau berita "XRP" itu harganya ambil dari id "ripple"
MAPPING_ID = {
    "binance-coin": "binancecoin",
    "xrp": "ripple",
    "pepecoin": "pepe",
    "toncoin": "the-open-network",
    "avalanche": "avalanche-2",
    "matic": "matic-network",
    "render": "render-token"
}

# 4. KONFIGURASI RADAR AIRDROP
# Tag berita yang mau dimata-matai
TAGS_AIRDROP = ["airdrop", "altcoin", "defi", "gamefi"]
# Kata kunci "Uang" (Kalau ketemu ini di judul, langsung lapor!)
KEYWORDS_CUAN = ["airdrop", "snapshot", "claim", "listing", "binance", "launchpad", "reward", "testnet"]

class CryptoUltimateBot:
    def __init__(self):
        print("🤖 Menyalakan Mesin AI (FinBERT)...")
        try:
            self.analyzer = pipeline("sentiment-analysis", model="ProsusAI/finbert")
        except Exception as e:
            print(f"❌ Gagal load model AI: {e}")
            sys.exit()

    def kirim_telegram(self, pesan):
        if "ISI_TOKEN" in TOKEN:
            print("⚠️ Token belum diisi! Skip kirim Telegram.")
            return
        
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": ID_TUJUAN, "text": pesan, "parse_mode": "Markdown"}
        try:
            requests.post(url, data=data)
            print("📨 Pesan terkirim!")
        except Exception as e:
            print(f"❌ Gagal kirim: {e}")

    def ambil_harga_semua(self):
        """Mengambil harga semua koin dalam 1 kali request (Hemat Waktu)"""
        print("💰 Mengambil data harga pasar...")
        
        # Kumpulkan semua ID CoinGecko yang valid
        list_id_gecko = []
        for c in COINS:
            real_id = MAPPING_ID.get(c, c)
            list_id_gecko.append(real_id)
            
        ids_string = ",".join(list_id_gecko)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_string}&vs_currencies=usd&include_24hr_change=true"
        
        try:
            # Timeout 10 detik agar tidak hang
            return requests.get(url, timeout=10).json()
        except Exception as e:
            print(f"❌ Gagal ambil harga: {e}")
            return {}

    def scraping_berita(self, tag):
        """Ambil judul berita dari Cointelegraph"""
        # Cek apakah tag perlu dibalik (misal: ripple -> xrp) untuk URL berita
        tag_url = tag
        for k, v in MAPPING_ID.items():
            if v == tag: tag_url = k
            
        url = f"https://cointelegraph.com/tags/{tag_url}"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all("span", class_="post-card-inline__title")
            # Ambil 2 berita terbaru saja
            return [item.get_text().strip() for item in items[:2]]
        except:
            return []

    def jalankan_radar_airdrop(self):
        """Mencari kata kunci cuan di berita altcoin/airdrop"""
        print("📡 Scanning peluang Airdrop...")
        laporan_airdrop = ""
        ada_temuan = False
        
        for tag in TAGS_AIRDROP:
            berita_list = self.scraping_berita(tag)
            for judul in berita_list:
                judul_lower = judul.lower()
                # Jika ada kata kunci sakti
                if any(k in judul_lower for k in KEYWORDS_CUAN):
                    laporan_airdrop += f"🎁 {judul}\n"
                    ada_temuan = True
        
        if ada_temuan:
            return "\n----------------------------------\n🔥 *RADAR AIRDROP & LISTING*\n" + laporan_airdrop
        return ""

    def mulai_patroli(self):
        # 1. Setup Waktu Indonesia (Sesuaikan jam server)
        # UTC+7 (WIB) atau UTC+8 (WITA). Default saya set UTC+7.
        waktu = datetime.datetime.now() + datetime.timedelta(hours=7)
        jam_str = waktu.strftime('%H:%M')
        tgl_str = waktu.strftime('%d-%m-%Y')
        
        print(f"\n🚀 START PATROLI: {tgl_str} {jam_str}")
        
        # 2. Ambil Harga
        data_harga = self.ambil_harga_semua()
        
        # 3. Siapkan Header Laporan
        laporan_final = f"🤖 *UPDATE PASAR CRYPTO*\n📅 {tgl_str} | ⏰ {jam_str} WIB\n"
        laporan_final += "----------------------------------\n"
        
        jumlah_sinyal = 0
        
        # 4. Loop Analisis Koin Utama
        for raw_coin in COINS:
            # Ambil ID yang benar
            coin_id = MAPPING_ID.get(raw_coin, raw_coin)
            
            # Ambil Harga & Persen Change
            info = data_harga.get(coin_id, {})
            harga = info.get('usd', 0)
            change = info.get('usd_24h_change', 0)
            
            # Format tampilan harga
            icon_hrg = "🟢" if change >= 0 else "🔴"
            str_harga = f"${harga:,.2f} ({icon_hrg}{change:.2f}%)"
            
            # Analisis Berita (AI)
            print(f"🔍 Cek Sentimen: {raw_coin.upper()}...", end="\r")
            berita = self.scraping_berita(raw_coin)
            
            sentiment_score = 0
            detail_berita = ""
            
            for judul in berita:
                hasil = self.analyzer(judul)[0]
                label = hasil['label']
                
                if label == 'positive': sentiment_score += 1
                elif label == 'negative': sentiment_score -= 1
                
                # Simpan judul hanya jika sentimennya kuat
                if label != 'neutral':
                    icon_news = "📈" if label == 'positive' else "📉"
                    detail_berita += f"{icon_news} {judul[:35]}...\n"

            # FILTER LAPORAN:
            # Lapor jika: Sentimen TIDAK Netral ATAU Harga bergerak > 3%
            is_volatile = abs(change) > 3.0
            is_significant = sentiment_score != 0
            
            if is_significant or is_volatile:
                status = "NETRAL 💤"
                if sentiment_score > 0: status = "BULLISH 🔥"
                elif sentiment_score < 0: status = "BEARISH 🩸"
                
                laporan_final += f"\n🪙 *{raw_coin.upper()}*\n💵 {str_harga}\nSinyal: {status}\n{detail_berita}"
                jumlah_sinyal += 1

        # 5. Jalankan Radar Airdrop (Opsi 2)
        info_airdrop = self.jalankan_radar_airdrop()
        if info_airdrop:
            laporan_final += info_airdrop
            jumlah_sinyal += 1

        # 6. Kirim Laporan
        print("\n✅ Analisis Selesai.")
        
        if jumlah_sinyal > 0:
            self.kirim_telegram(laporan_final)
        else:
            print("💤 Pasar sepi, tidak ada laporan.")
            # Opsional: Aktifkan baris bawah jika mau tetap lapor meski sepi
            # self.kirim_telegram(f"🤖 Laporan {jam_str}: Pasar Sideways/Sepi. Tidak ada sinyal.")

if __name__ == "__main__":
    bot = CryptoUltimateBot()
    bot.mulai_patroli()
