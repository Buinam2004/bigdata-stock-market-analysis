# Stock Data Streaming Pipeline

Dự án streaming dữ liệu chứng khoán real-time từ Yahoo Finance → MongoDB Atlas → Apache Kafka.

## Kiến trúc hệ thống

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Yahoo Finance  │───▶│  MongoDB Atlas  │───▶│  Apache Kafka   │
│   (yfinance)    │    │ (Change Stream) │    │   (Producer)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
     crawl_data.py           ▲                   mongo_to_kafka.py
                             │
                      Watch Changes
```

## Yêu cầu hệ thống

- Windows 10/11 (64-bit)
- Python 3.8+
- Docker Desktop
- Kết nối Internet

---

## Phần 1: Cài đặt Docker Desktop

### Bước 1: Tải Docker Desktop

1. Truy cập: https://www.docker.com/products/docker-desktop/
2. Click **"Download for Windows"**
3. Chạy file `Docker Desktop Installer.exe`

### Bước 2: Cài đặt Docker Desktop

1. Chạy installer và chọn **"Use WSL 2 instead of Hyper-V"** (khuyến nghị)
2. Click **Install**
3. Khởi động lại máy tính nếu được yêu cầu

### Bước 3: Kiểm tra cài đặt

Mở **Command Prompt** hoặc **PowerShell** và chạy:

```bash
docker --version
docker-compose --version
```

Kết quả mong đợi:

```
Docker version 24.x.x, build xxxxxxx
Docker Compose version v2.x.x
```

### Bước 4: Khởi động Docker Desktop

1. Mở **Docker Desktop** từ Start Menu
2. Đợi đến khi icon Docker ở system tray chuyển sang màu xanh (Running)

---

## Phần 2: Cài đặt Python và Dependencies

### Bước 1: Cài đặt Python (nếu chưa có)

1. Tải Python từ: https://www.python.org/downloads/
2. **Quan trọng**: Tick chọn **"Add Python to PATH"** khi cài đặt

### Bước 2: Tạo Virtual Environment (Khuyến nghị)

```bash
# Di chuyển đến thư mục dự án
cd D:\Bigdata

# Tạo virtual environment
python -m venv venv

# Kích hoạt virtual environment
# Windows CMD:
venv\Scripts\activate

# Windows PowerShell:
.\venv\Scripts\Activate.ps1
```

### Bước 3: Cài đặt thư viện Python

```bash
pip install yfinance pymongo kafka-python
```

Hoặc tạo file `requirements.txt` và cài đặt:

```bash
# Tạo requirements.txt với nội dung:
# yfinance
# pymongo
# kafka-python

pip install -r requirements.txt
```

---

## Phần 3: Khởi động Kafka với Docker

### Bước 1: Khởi động Zookeeper và Kafka

Mở terminal tại thư mục dự án và chạy:

```bash
cd D:\Bigdata
docker-compose up -d
```

### Bước 2: Kiểm tra containers đang chạy

```bash
docker ps
```

Kết quả mong đợi:

```
CONTAINER ID   IMAGE                             STATUS          PORTS
xxxxxxxxxxxx   confluentinc/cp-kafka:7.5.0      Up X minutes    0.0.0.0:9092->9092/tcp
xxxxxxxxxxxx   confluentinc/cp-zookeeper:7.5.0  Up X minutes    0.0.0.0:2181->2181/tcp
```

### Bước 3: Tạo Kafka Topic

```bash
# Vào container Kafka
docker exec -it kafka bash

# Tạo topic "stock-trades-stream"
kafka-topics --create --topic stock-trades-stream --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

# Kiểm tra topic đã tạo
kafka-topics --list --bootstrap-server localhost:9092

# Thoát container
exit
```

---

## Phần 4: Chạy Pipeline

### Bước 1: Chạy Crawl Data (Terminal 1)

Mở terminal mới:

```bash
cd D:\Bigdata
# Kích hoạt venv nếu dùng
venv\Scripts\activate

python crawl_data.py
```

Kết quả mong đợi:

```
START STREAMING STOCK DATA TO MONGODB ATLAS
Inserted AAPL | 2026-01-05T10:30:00.000000
Inserted MSFT | 2026-01-05T10:30:00.500000
...
Sleeping 10 seconds...
```

### Bước 2: Chạy MongoDB to Kafka Producer (Terminal 2)

Mở terminal mới:

```bash
cd D:\Bigdata
# Kích hoạt venv nếu dùng
venv\Scripts\activate

python mongo_to_kafka.py
```

Kết quả mong đợi:

```
Listening MongoDB Change Stream...
Sent to Kafka: AAPL @ 2026-01-05T10:30:00.000000
Sent to Kafka: MSFT @ 2026-01-05T10:30:00.500000
...
```

### Bước 3: Kiểm tra dữ liệu trong Kafka (Terminal 3)

```bash
# Vào container Kafka
docker exec -it kafka bash

# Consume messages từ topic
kafka-console-consumer --topic stock-trades-stream --from-beginning --bootstrap-server localhost:9092
```

Kết quả mong đợi:

```json
{
  "symbol": "AAPL",
  "sector": "Technology",
  "open": 150.5,
  "high": 151.2,
  "low": 149.8,
  "close": 150.9,
  "volume": 1234567,
  "timestamp": "2026-01-05T10:30:00.000000",
  "source": "yahoo_finance"
}
```

---

## Dừng hệ thống

### Dừng Python scripts

Nhấn `Ctrl + C` trong các terminal đang chạy Python

### Dừng Docker containers

```bash
cd D:\Bigdata
docker-compose down
```

### Dừng và xóa toàn bộ data

```bash
docker-compose down -v
```

---

## Danh sách cổ phiếu được theo dõi

| Sector     | Symbols                       |
| ---------- | ----------------------------- |
| Technology | AAPL, MSFT, GOOGL, META, NVDA |
| Banking    | JPM, BAC, WFC, C, GS          |
| Energy     | XOM, CVX, BP, SHEL            |
| Healthcare | JNJ, PFE, MRK, ABBV           |
| Retail     | AMZN, WMT, COST, HD, MCD      |
| ETF        | SPY, QQQ, DIA                 |

---

## Cấu trúc dự án

```
D:\Bigdata\
├── crawl_data.py       # Crawl dữ liệu từ Yahoo Finance → MongoDB
├── mongo_to_kafka.py   # Stream từ MongoDB → Kafka
├── docker-compose.yml  # Cấu hình Docker cho Kafka & Zookeeper
├── requirements.txt    # Python dependencies
└── README.md           # File hướng dẫn này
```

---

## Ghi chú

- **MongoDB Atlas**: Dự án sử dụng MongoDB Atlas (cloud). Không cần cài MongoDB local.
- **Change Stream**: Yêu cầu MongoDB Replica Set (Atlas đã có sẵn).
- **Thời gian crawl**: Mặc định 10 giây/lần. Có thể thay đổi `SLEEP_TIME` trong `crawl_data.py`.

---

## Quick Start (TL;DR)

```bash
# 1. Cài Docker Desktop và khởi động

# 2. Cài Python dependencies
pip install yfinance pymongo kafka-python

# 3. Khởi động Kafka
cd D:\Bigdata
docker-compose up -d

# 4. Tạo topic (đợi 30s sau khi docker-compose up)
docker exec -it kafka kafka-topics --create --topic stock-trades-stream --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

# 5. Chạy crawl data (Terminal 1)
python crawl_data.py

# 6. Chạy mongo to kafka (Terminal 2)
python mongo_to_kafka.py

# 7. Verify (Terminal 3)
docker exec -it kafka kafka-console-consumer --topic stock-trades-stream --from-beginning --bootstrap-server localhost:9092
```

---
