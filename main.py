import requests
import pandas as pd
import time
import os

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def get_data():
    try:
        url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=100"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            print("API ERROR:", response.text)
            return pd.DataFrame()

        data = response.json()

        if not data or isinstance(data, dict):
            print("Data kosong / error dari API")
            return pd.DataFrame()

        df = pd.DataFrame(data, columns=[
            "time","open","high","low","close","volume",
            "close_time","qav","trades","tbbav","tbqav","ignore"
        ])

        df["close"] = df["close"].astype(float)
        return df

    except Exception as e:
        print("GET DATA ERROR:", e)
        return pd.DataFrame()


def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print("TELEGRAM ERROR:", e)


while True:
    try:
        df = get_data()

        # 🔴 CEK DATA KOSONG
        if df.empty:
            print("Data kosong, retry 1 menit...")
            time.sleep(60)
            continue

        df["RSI"] = calculate_rsi(df)

        # 🔴 CEK RSI VALID
        if df["RSI"].dropna().empty:
            print("RSI belum siap")
            time.sleep(60)
            continue

        rsi = df["RSI"].dropna().iloc[-1]

        # SIGNAL
        if rsi < 30:
            signal = "BUY"
        elif rsi > 70:
            signal = "SELL"
        else:
            signal = "HOLD"

        message = f"BTC/USDT\nRSI: {rsi:.2f}\nSignal: {signal}"
        print(message)
        send_message(message)

    except Exception as e:
        print("MAIN LOOP ERROR:", e)

    time.sleep(3600)
