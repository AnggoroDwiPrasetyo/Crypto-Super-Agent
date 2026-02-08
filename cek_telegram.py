import requests

# --- ISI DENGAN DATA KAMU ---
TOKEN = "8468708708:AAENxzRgZN9_6vAbutadPVFB7jfmP4lfExA" 
CHAT_ID = "1902304881" 

def tes_kirim():
    pesan = "Halo! Jika ini masuk, berarti setinganmu sudah benar. 🚀"
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": pesan}
    
    # Kita minta respon lengkap dari Telegram
    response = requests.post(url, data=data)
    
    print("Status Code:", response.status_code)
    print("Respon Telegram:", response.json())

if __name__ == "__main__":
    tes_kirim()