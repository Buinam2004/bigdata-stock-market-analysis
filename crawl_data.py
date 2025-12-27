import time
from datetime import datetime
import yfinance as yf
from pymongo import MongoClient


# MongoDB Atlas connection string
MONGO_URI = "mongodb+srv://stock_user:20225211@cluster0.ejcendu.mongodb.net/?appName=Cluster0"

DB_NAME = "stock_streaming"
COLLECTION_NAME = "stock_prices"

# Chu kỳ ghi dữ liệu (giây)
SLEEP_TIME = 10

# DANH SÁCH CỔ PHIẾU (ĐA LĨNH VỰC)

SYMBOLS = [
    # Technology
    "AAPL", "MSFT", "GOOGL", "META", "NVDA",

    # Banking
    "JPM", "BAC", "WFC", "C", "GS",

    # Energy
    "XOM", "CVX", "BP", "SHEL",

    # Healthcare
    "JNJ", "PFE", "MRK", "ABBV",

    # Retail
    "AMZN", "WMT", "COST", "HD", "MCD",

    # ETF
    "SPY", "QQQ", "DIA"
]

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
    "DIA": "ETF"
}

# KẾT NỐI MONGODB ATLAS

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Tạo index
collection.create_index([("symbol", 1)])
collection.create_index([("timestamp", 1)])

print("START STREAMING STOCK DATA TO MONGODB ATLAS")

# STREAMING LOOP

while True:
    for symbol in SYMBOLS:
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")

            if data.empty:
                print(f"No data for {symbol}")
                continue

            latest = data.iloc[-1]

            document = {
                "symbol": symbol,
                "sector": SECTOR_MAP.get(symbol, "Unknown"),
                "open": float(latest["Open"]),
                "high": float(latest["High"]),
                "low": float(latest["Low"]),
                "close": float(latest["Close"]),
                "volume": int(latest["Volume"]),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "yahoo_finance"
            }

            collection.insert_one(document)
            print(f"Inserted {symbol} | {document['timestamp']}")

        except Exception as e:
            print(f"Error with {symbol}: {e}")

    print(f"Sleeping {SLEEP_TIME} seconds...\n")
    time.sleep(SLEEP_TIME)
