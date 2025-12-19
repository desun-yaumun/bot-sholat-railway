import os
import time
import requests
import logging
from datetime import datetime, date, timedelta

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))
STICKER_ID = os.getenv("STICKER_ID")

CITY = "Bintan"
COUNTRY = "Indonesia"
CHECK_INTERVAL = 30  # detik

# === OVERRIDE MANUAL (kosongkan {} kalau tidak dipakai)
MANUAL_OVERRIDE = {
    # "Subuh": "04:33",
    # "Dzuhur": "11:50",
}

# =========================================

logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url, data=data, timeout=10)
        return r.ok
    except Exception as e:
        logging.error(f"Telegram error: {e}")
        return False


def send_sticker(sticker_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendSticker"
    data = {
        "chat_id": CHAT_ID,
        "sticker": sticker_id
    }
    try:
        r = requests.post(url, data=data, timeout=10)
        return r.ok
    except Exception as e:
        logging.error(f"Sticker error: {e}")
        return False


def get_jadwal_sholat():
    today = date.today().strftime("%d-%m-%Y")
    url = f"https://api.aladhan.com/v1/timingsByCity/{today}"
    params = {
        "city": CITY,
        "country": COUNTRY,
        "method": 11
    }

    r = requests.get(url, params=params, timeout=10)
    data = r.json()["data"]["timings"]

    jadwal = {
        "Subuh": data["Fajr"][:5],
        "Dzuhur": data["Dhuhr"][:5],
        "Ashar": data["Asr"][:5],
        "Maghrib": data["Maghrib"][:5],
        "Isya": data["Isha"][:5],
    }

    # override manual
    for k, v in MANUAL_OVERRIDE.items():
        jadwal[k] = v

    return jadwal

def menit_sebelum(jam, menit=10):
    t = datetime.strptime(jam, "%H:%M") - timedelta(minutes=menit)
    return t.strftime("%H:%M")

def main():
    logging.info("BOT STARTED")
    send_telegram("✅ Bot sholat Bintan aktif")

    jadwal = {}
    last_date = None
    sent_flags = set()

    while True:
        try:
            now = datetime.now()
            today = now.date()
            now_str = now.strftime("%H:%M")

            # 🔄 Ambil jadwal baru setiap ganti hari
            if today != last_date:
                jadwal = get_jadwal_sholat()
                sent_flags.clear()
                last_date = today
                logging.info(f"Jadwal hari ini: {jadwal}")

            # 🔁 Cek tiap waktu sholat
            for sholat, jam in jadwal.items():
                sebelum = menit_sebelum(jam, 10)

                # ⏰ 10 MENIT SEBELUM SHOLAT
                if now_str == sebelum and f"{sholat}_before" not in sent_flags:
                    send_sticker(STICKER_ID)
                    send_telegram(
                        f"⏰ 10 menit lagi waktu *{sholat}*\n📍 Bintan\n⏰ {jam}"
                    )
                    sent_flags.add(f"{sholat}_before")
                    logging.info(f"Reminder 10 menit sebelum {sholat}")

                # 🕌 TEPAT WAKTU SHOLAT (INI YANG KAMU TANYAKAN)
                if now_str == jam and sholat not in sent_flags:
                    send_sticker(STICKER_ID)  # ✅ STICKER MUNCUL BERSAMA WAKTU SHOLAT
                    send_telegram(
                        f"🕌 Waktu *{sholat}* Telah Tiba\n📍 Untuk Wilayah Kab.Bintan dan Sekitarnya\n⏰ {jam}"
                    )
                    sent_flags.add(sholat)
                    logging.info(f"Waktu sholat {sholat} terkirim")

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            with open("error.log", "a") as f:
                f.write(f"{datetime.now()} ERROR: {e}\n")
            time.sleep(10)

if __name__ == "__main__":
    main()
