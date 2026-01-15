"""
Yahoo Finance -> Kafka Streaming Producer
- Thu thap du lieu gia co phieu tu Yahoo Finance
- Gui moi ban ghi gia co phieu nhu 1 event vao Kafka
"""

import os
import time
import json
from datetime import datetime
import yfinance as yf
from kafka import KafkaProducer

# Danh sach stock symbols
SYMBOLS = [
    # Technology
    "AAPL",
    "MSFT",
    "GOOGL",
    "META",
    "NVDA",
    # Banking
    "JPM",
    "BAC",
    "WFC",
    "C",
    "GS",
    # Energy
    "XOM",
    "CVX",
    "BP",
    "SHEL",
    # Healthcare
    "JNJ",
    "PFE",
    "MRK",
    "ABBV",
    # Retail
    "AMZN",
    "WMT",
    "COST",
    "HD",
    "MCD",
    # ETF
    "SPY",
    "QQQ",
    "DIA",
]

# Mapping sector cho tung symbol
SECTOR_MAP = {
    # Technology
    "AAPL": "Technology",
    "MSFT": "Technology",
    "GOOGL": "Technology",
    "META": "Technology",
    "NVDA": "Technology",
    # Banking
    "JPM": "Banking",
    "BAC": "Banking",
    "WFC": "Banking",
    "C": "Banking",
    "GS": "Banking",
    # Energy
    "XOM": "Energy",
    "CVX": "Energy",
    "BP": "Energy",
    "SHEL": "Energy",
    # Healthcare
    "JNJ": "Healthcare",
    "PFE": "Healthcare",
    "MRK": "Healthcare",
    "ABBV": "Healthcare",
    # Retail
    "AMZN": "Retail",
    "WMT": "Retail",
    "COST": "Retail",
    "HD": "Retail",
    "MCD": "Retail",
    # ETF
    "SPY": "ETF",
    "QQQ": "ETF",
    "DIA": "ETF",
}

# Get Kafka bootstrap servers from environment or default to localhost
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# Khoi tao Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)


def fetch_latest_price(symbol):
    """
    Lay gia co phieu moi nhat tu Yahoo Finance
    """
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="1m")

        # Khong co du lieu
        if data is None or data.empty:
            return None

        latest = data.iloc[-1]

        # Co candle nhung gia bi null
        if latest.isnull().any():
            return None

        # Use current time instead of candle timestamp for real-time uniqueness
        # This ensures each fetch has a unique event_time for proper windowing
        current_time = datetime.now()

        return {
            "symbol": symbol,
            "sector": SECTOR_MAP.get(symbol, "Unknown"),
            "open": float(latest["Open"]),
            "high": float(latest["High"]),
            "low": float(latest["Low"]),
            "close": float(latest["Close"]),
            "volume": int(latest["Volume"]),
            "event_time": current_time.isoformat(),  # Use current time for uniqueness
            "source": "yahoo_finance",
        }

    except Exception as e:
        print(f"Fetch error for {symbol}: {e}")
        return None


# Thoi gian sleep giua cac lan fetch (giay)
SLEEP_TIME = 5  # Reduced to 1 second for near real-time

print("START STREAMING STOCK DATA TO KAFKA")
print(f"Topic: stock_ticks | Symbols: {len(SYMBOLS)} | Interval: {SLEEP_TIME}s")
print("Press Ctrl+C to stop.\n")

try:
    while True:
        success_count = 0
        fail_count = 0

        for symbol in SYMBOLS:
            try:
                event = fetch_latest_price(symbol)

                if event is None:
                    fail_count += 1
                    continue

                producer.send("stock_ticks", event)
                success_count += 1

            except Exception as e:
                fail_count += 1

        time.sleep(SLEEP_TIME)

except KeyboardInterrupt:
    print("\nStopping producer...")
    producer.flush()
    producer.close()
    print("Producer stopped!")
