import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import os
import time
import datetime
import sys

# ==========================================
# KONFIGURASI PRIBADI 
# ==========================================
TOKEN = os.environ.get("TOKEN_TELEGRAM") or TOKEN_TELEGRAM
ID_TUJUAN = os.environ.get("CHAT_ID") or CHAT_ID

# ==========================================
# DAFTAR PANTAUAN (ULTIMATE LIST 30+ KOIN)
# ==========================================
COINS = [
    # --- 👑 THE KINGS (Market Movers) ---
    "bitcoin", "ethereum", "binance-coin", "solana", "xrp",
    
    # --- 🐸 MEME COINS (High Volatility) ---
    "dogecoin", "shiba-inu", "pepecoin", "bonk", "floki", "dogwifhat",
    
    # --- 🤖 AI & DATA (Trending Sektor) ---
    "artificial-intelligence", # Tag gabungan berita AI
    "fetch-ai", "render-token", "near-protocol", "the-graph",
    
    # --- ⚡ LAYER 1 & INFRA (Fundamental) ---
    "sui", "sei", "aptos", "avalanche", "cardano", 
    "polkadot", "tron", "toncoin", "chainlink",
    
    # --- 🔗 DEFI & LAYER 2 ---
    "uniswap", "polygon", "arbitrum", "optimism", "litecoin"
]

class CryptoSuperAgent:
    def __init__(self):
        print("🤖 Menginisialisasi Otak AI (FinBERT)...")
        print("   (Ini mungkin memakan waktu 30-60 detik di awal)")
        try:
            self.analyzer = pipeline("sentiment-analysis", model="ProsusAI/finbert")
            print("✅ Model AI Siap!")
        except Exception as e:
            print(f"❌ Gagal load model: {e}")
            sys.exit()

    def kirim_telegram(self, pesan):
        """Mengirim pesan ke Telegram"""
        if "GANTI" in TOKEN or "GANTI" in ID_TUJUAN:
            print("❌ ERROR: Token/ID belum diisi! Edit file main.py dulu.")
            return

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": ID_TUJUAN, "text": pesan, "parse_mode": "Markdown"}
        
        try:
            requests.post(url, data=data)
            print("📨 Laporan terkirim ke Telegram.")
        except Exception as e:
            print(f"❌ Gagal kirim Telegram: {e}")

    def baca_berita(self, coin):
        """Membaca berita terbaru dari Cointelegraph"""
        url = f"https://cointelegraph.com/tags/{coin}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            headlines = []
            
            # Cari elemen judul berita (selector bisa berubah tergantung website)
            items = soup.find_all("span", class_="post-card-inline__title")
            
            # Ambil maksimal 2 berita terbaru per koin agar proses cepat
            for item in items[:2]:
                text = item.get_text().strip()
                headlines.append(text)
                
            return headlines
        except Exception as e:
            # Error silent agar tidak mengganggu loop koin lain
            return []

    def jalankan_misi(self):
        # Tambah 7 jam untuk WIB, atau 8 jam untuk WITA
        waktu_skrg = (datetime.datetime.now() + datetime.timedelta(hours=7)).strftime('%d-%m-%Y %H:%M')
        print(f"\n🔍 MEMULAI PATROLI PASAR ({waktu_skrg})")
        print("=" * 40)
        
        laporan_final = f"🤖 *LAPORAN PASAR CRYPTO*\n📅 {waktu_skrg}\n"
        laporan_final += "----------------------------------\n"
        
        jumlah_sinyal = 0
        jumlah_netral = 0
        koin_diproses = 0

        for coin in COINS:
            koin_diproses += 1
            # Tampilkan progress di terminal (biar gak dikira hang)
            print(f"[{koin_diproses}/{len(COINS)}] Memantau: {coin.upper()}...", end="\r")
            
            berita_list = self.baca_berita(coin)
            if not berita_list: 
                continue

            score = 0
            detail_berita = ""
            
            # Analisa setiap judul berita
            for judul in berita_list:
                hasil = self.analyzer(judul)[0]
                label = hasil['label']
                
                # Scoring Sederhana
                if label == 'positive': 
                    score += 1
                    icon = "📈"
                elif label == 'negative': 
                    score -= 1
                    icon = "📉"
                else:
                    icon = "➖"
                
                # Simpan judul berita jika sentimennya KUAT (Bukan Netral)
                # Agar kita tau ALASAN kenapa dia Bullish/Bearish
                if label != 'neutral':
                    # Potong judul jika terlalu panjang (>40 karakter)
                    judul_pendek = (judul[:40] + '..') if len(judul) > 40 else judul
                    detail_berita += f"{icon} {judul_pendek}\n"

            # --- LOGIKA FILTER ---
            if score > 0:
                status = "BULLISH 🔥"
                laporan_final += f"\n🪙 *{coin.upper()}* -> {status}\n{detail_berita}"
                jumlah_sinyal += 1
            elif score < 0:
                status = "BEARISH 🩸"
                laporan_final += f"\n🪙 *{coin.upper()}* -> {status}\n{detail_berita}"
                jumlah_sinyal += 1
            else:
                jumlah_netral += 1
        
        print("\n" + "=" * 40)
        print("✅ Analisis Selesai.")

        # --- KIRIM LAPORAN ---
        # Kondisi 1: Ada sinyal kuat (Bullish/Bearish)
        if jumlah_sinyal > 0:
            laporan_final += "\n----------------------------------"
            laporan_final += f"\nℹ️ _Info: {jumlah_netral} koin lainnya sedang Netral (Wait & See)_"
            self.kirim_telegram(laporan_final)
        
        # Kondisi 2: Semua pasar Netral (Sepi)
        else:
            pesan_sepi = f"🤖 *LAPORAN PASAR SEPI*\n📅 {waktu_skrg}\n\nSemua {len(COINS)} koin terpantau NETRAL/SIDEWAYS.\nTidak ada gejolak berita signifikan."
            print("Pasar sepi, mengirim laporan singkat...")
            self.kirim_telegram(pesan_sepi)

# --- EKSEKUSI UTAMA ---
if __name__ == "__main__":
    agent = CryptoSuperAgent()
    agent.jalankan_misi()

    print("🏁 Program Selesai.")
