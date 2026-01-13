# HƯỚNG DẪN CHẠY PIPELINE: YAHOO FINANCE → KAFKA → SPARK → ICEBERG BRONZE (SPARK CHẠY LOCAL)

> **Pipeline**: Thu thập dữ liệu cổ phiếu real-time từ Yahoo Finance → Kafka → Spark Streaming → Iceberg Bronze Layer
>
> Hạ tầng (Kafka, MinIO) chạy bằng Docker. Code (producer + Spark) chạy trực tiếp trên máy local.

---

## PREREQUISITES - CHUẨN BỊ MÔI TRƯỜNG

### Yêu cầu hệ thống

| Component       | Version           | Link                                                                        |
| --------------- | ----------------- | --------------------------------------------------------------------------- |
| Java            | 11 hoặc 17        | [Oracle JDK](https://www.oracle.com/java/technologies/downloads/)           |
| Python          | 3.8+ nhỏ hơn 3.13 | [Python](https://www.python.org/downloads/)                                 |
| Apache Spark    | 3.5.7             | [Spark](https://spark.apache.org/downloads.html)                            |
| Docker Desktop  | Latest            | [Docker](https://www.docker.com/products/docker-desktop/)                   |
| Hadoop winutils | 3.3.6             | [GitHub](https://github.com/cdarlint/winutils/tree/master/hadoop-3.3.6/bin) |

### 🔧 Cài đặt nhanh

**1. Java & Spark**

```bash
# Kiểm tra Java
java -version  # Cần: 11.x hoặc 17.x

# Set biến môi trường (Windows)
JAVA_HOME=C:\Program Files\Java\jdk-17
SPARK_HOME=C:\spark-3.5.7-bin-hadoop3
HADOOP_HOME=%SPARK_HOME%\hadoop
Path=%JAVA_HOME%\bin;%SPARK_HOME%\bin;%Path%

# Download hadoop.dll + winutils.exe → C:\spark-3.5.7-bin-hadoop3\hadoop\bin\
```

**2. Python packages**

```bash
pip install yfinance kafka-python pyspark
python --version  # Cần: 3.8+
```

**3. Docker**

```bash
docker --version
docker-compose --version
```

**4. Visual C++ Runtime (nếu lỗi MSVCR100.dll)**

```bash
winget install Microsoft.VCRedist.2010.x64
```

---

## SETUP DOCKER SERVICES

### 1. Tạo file docker-compose.yml

**File đã có tại:** `d:/bigdata-stock-market-analysis/docker-compose.yml`

**Nội dung:**

```yaml
version: "3"
services:
  kafka:
    image: confluentinc/cp-kafka:latest
    ports:
      - "9092:9092"
    environment:
      # KRaft mode (no ZooKeeper)
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_KRAFT_CLUSTER_ID: "q1Sh-9_ISia_zwGINzRvyQ"
      KAFKA_CONTROLLER_QUORUM_VOTERS: "1@kafka:29093"

      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: "CONTROLLER:PLAINTEXT,INTERNAL:PLAINTEXT,EXTERNAL:PLAINTEXT"
      KAFKA_LISTENERS: "INTERNAL://kafka:29092,EXTERNAL://0.0.0.0:9092,CONTROLLER://kafka:29093"
      KAFKA_ADVERTISED_LISTENERS: "INTERNAL://kafka:29092,EXTERNAL://localhost:9092"
      KAFKA_INTER_BROKER_LISTENER_NAME: "INTERNAL"
      KAFKA_CONTROLLER_LISTENER_NAMES: "CONTROLLER"

      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1

  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
```

### 2. Khởi động Docker services

```bash
cd d:/bigdata-stock-market-analysis
docker compose up -d
```

### 3. Verify services đang chạy

```bash
docker ps
```

**Kết quả mong đợi:**

```
NAMES       STATUS          PORTS
kafka       Up X minutes    0.0.0.0:9092->9092/tcp
minio       Up X minutes    0.0.0.0:9000-9001->9000-9001/tcp
```

### 4. Tạo Kafka topic (chỉ lần đầu)

```bash
docker exec kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic stock_ticks \
  --partitions 1 \
  --replication-factor 1
```

**Verify topic:**

```bash
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
# Phải thấy: stock_ticks
```

---

## PHASE 2: YAHOO FINANCE → KAFKA PRODUCER

### Mục tiêu

Thu thập dữ liệu cổ phiếu từ Yahoo Finance  
Gửi vào Kafka topic `stock_ticks` mỗi 30 giây

### TERMINAL 1: Chạy Producer

**Mở Terminal 1:**

```bash
cd d:/bigdata-stock-market-analysis/raw_data_bronze
python yahoo_to_kafka.py
```

**Expected Output:**

```
============================================================
START STREAMING STOCK DATA TO KAFKA
Topic: stock_ticks
Symbols: 29 stocks (AAPL, MSFT, GOOGL, META, TSLA...)
Interval: 30 seconds
============================================================

[2026-01-10 14:30:00] Fetching data...
  [OK] AAPL   | Technology | $259.35
  [OK] MSFT   | Technology | $479.20
  [OK] GOOGL  | Technology | $328.48
  ...
Successfully sent 29 stocks to Kafka!

[2026-01-10 14:30:30] Fetching data...
  [OK] AAPL   | Technology | $259.42
  ...
```

**ĐỂ TERMINAL NÀY CHẠY LIÊN TỤC!**

---

### TERMINAL 2: Test Spark Streaming

**Mở Terminal mới (Terminal 2):**

```bash
cd d:/bigdata-stock-market-analysis/raw_data_bronze
spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.7 \
  kafka_to_spark.py
```

** Expected Output (rút gọn):**

```
PHASE 3: Kafka -> Spark Structured Streaming
SparkSession initialized!

Parsed DataFrame Schema:
root
 |-- symbol: string
 |-- sector: string
 |-- close: double
 |-- volume: long
 |-- event_time: string

Batch: 0
+------+----------+--------+-------+
|symbol|sector    |close   |volume |
+------+----------+--------+-------+
|AAPL  |Technology|259.35  |318089 |
|MSFT  |Technology|479.20  |184154 |
+------+----------+--------+-------+
```

**Nếu thấy data streaming → PHASE 3 PASSED!**

- Phase 3 CHỈ ĐỂ TEST - Có thể:\*\*

* **Option 1**: Nhấn Ctrl+C dừng, chuyển sang Phase 4 (khuyến nghị)
* **Option 2**: Để chạy tiếp (monitor data), chạy Phase 4 ở Terminal 3
* **Option 3**: Bỏ qua Phase 3, chạy thẳng Phase 4 luôn

---

## PHASE 4: SPARK → ICEBERG BRONZE (NHIỆM VỤ CHÍNH)

```
============================================================
PHASE 3: Kafka -> Spark Structured Streaming
============================================================
SparkSession initialized!

Reading streaming data from Kafka topic: stock_ticks

Parsed DataFrame Schema:
root
 |-- symbol: string (nullable = true)
 |-- sector: string (nullable = true)
 |-- open: double (nullable = true)
 |-- high: double (nullable = true)
 |-- low: double (nullable = true)
 |-- close: double (nullable = true)
 |-- volume: long (nullable = true)
 |-- event_time: string (nullable = true)
 |-- source: string (nullable = true)

Starting streaming query to console...
Press Ctrl+C to stop.

-------------------------------------------
Batch: 0
-------------------------------------------
+------+----------+------------------+-------+-------------------------+
|symbol|sector    |close             |volume |event_time               |
+------+----------+------------------+-------+-------------------------+
|AAPL  |Technology|259.3500061035156 |318089 |2026-01-10T15:59:00-05:00|
|MSFT  |Technology|479.20001220703125|184154 |2026-01-10T15:59:00-05:00|
|GOOGL |Technology|328.4800109863281 |219387 |2026-01-10T15:59:00-05:00|
|META  |Technology|653.0399780273438 |114756 |2026-01-10T15:59:00-05:00|
|NVDA  |Technology|184.85000610351562|1018063|2026-01-10T15:59:00-05:00|
...
+------+----------+------------------+-------+-------------------------+
```

### Tiêu chí Pass Phase 3

- [x] Spark job chạy không lỗi
- [x] Không lỗi schema (thấy root schema với 9 columns)
- [x] DataFrame hiển thị đúng dữ liệu (symbol, sector, close, volume, event_time)

**Nếu thấy dữ liệu streaming → PHASE 3 PASSED!**

**Nhấn Ctrl+C để dừng Terminal 2, chuẩn bị Phase 4**

---

## PHASE 4: SPARK → ICEBERG BRONZE (NHIỆM VỤ CHÍNH)

### Mục tiêu

Ghi dữ liệu streaming vào Iceberg  
Tạo bảng stock_bronze với cột ingest_time và source

### TERMINAL 2 (hoặc Terminal 3 nếu giữ Phase 3)

**Chạy Phase 4:**

```bash
cd d:/bigdata-stock-market-analysis/raw_data_bronze
spark-submit \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.7,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.367 \
  --conf spark.hadoop.fs.s3a.endpoint=http://localhost:9000 \
  --conf spark.hadoop.fs.s3a.access.key=minioadmin \
  --conf spark.hadoop.fs.s3a.secret.key=minioadmin \
  --conf spark.hadoop.fs.s3a.path.style.access=true \
  --conf spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem \
  --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false \
  spark_to_iceberg_bronze.py
```

> **Lưu ý:** Phase 3 và Phase 4 CÓ THỂ chạy đồng thời (cùng đọc từ Kafka topic `stock_ticks`)

** Expected Output (rút gọn):**

```
PHASE 4: Spark Streaming -> Iceberg Bronze
SparkSession with Iceberg initialized!
Warehouse: D:/Bigdata/iceberg-warehouse

Table stock_bronze created successfully!

Streaming to Iceberg Bronze STARTED!
Data is being written to: iceberg-warehouse/stock_db/stock_bronze
```

**ĐỂ TERMINAL NÀY CHẠY LIÊN TỤC!**

### ĐỢI 2-3 PHÚT

Dữ liệu sẽ tích lũy ~60-90 records (29 stocks x 3 batches)

---

## PHASE 5: VERIFY ICEBERG (TÙY CHỌN)

````

**ĐỂ TERMINAL NÀY CHẠY, KHÔNG TẮT!**

---

### ĐỢI 2-3 PHÚT

**Để pipeline tích lũy dữ liệu:**

- Producer (Terminal 1) gửi data mỗi 30 giây
- Spark (Terminal 2) xử lý theo micro-batch
- Iceberg ghi vào warehouse

**Sau 2-3 phút, sẽ có ~60-90 records trong bảng**

---

## PHASE 5: VERIFY ICEBERG BRONZE (XÁC MINH DỮ LIỆU)

### Mục tiêu

Kiểm tra dữ liệu đã ghi vào Iceberg
Xác minh schema, partitions, và data quality

### TERMINAL 3: Mở terminal mới

**MỞ TERMINAL MỚI (thứ 3) để không làm gián đoạn Terminal 1 & 2**

```bash
cd d:/bigdata-stock-market-analysis/raw_data_bronze
spark-submit \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.367 \
  --conf spark.hadoop.fs.s3a.endpoint=http://localhost:9000 \
  --conf spark.hadoop.fs.s3a.access.key=minioadmin \
  --conf spark.hadoop.fs.s3a.secret.key=minioadmin \
  --conf spark.hadoop.fs.s3a.path.style.access=true \
  --conf spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem \
  --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false \
  query_iceberg_bronze.py
````

---

## TỔNG KẾT PIPELINE END-TO-END

```
Yahoo Finance → Kafka → Spark Streaming → Iceberg Bronze
```

### Cấu trúc project

```
D:/Bigdata/
├── docker-compose.yml              # Kafka (KRaft, no ZooKeeper) + MinIO
├── yahoo_to_kafka.py              # Phase 2: Producer
├── kafka_to_spark.py              # Phase 3: Test streaming
├── spark_to_iceberg_bronze.py     # Phase 4: Ghi vào Iceberg
├── query_iceberg_bronze.py        # Phase 5: Verify (optional)
├── iceberg-warehouse/             # Iceberg data lake
│   └── stock_db/
│       └── stock_bronze/           # Bảng Bronze
└── checkpoints/                   # Spark checkpoints
```

### Dừng pipeline

```bash
# Terminal 1: Ctrl+C (dừng Producer)
# Terminal 2: Ctrl+C (dừng Spark streaming)

# Dừng Docker
docker-compose down
```

---

## TROUBLESHOOTING (LỖI THƯỜNG GẶP)

### 1. Kafka connection refused

**Triệu chứng:** `Connection refused to localhost:9092`

```bash
docker ps                  # Kiểm tra Kafka chạy chưa
docker-compose up -d       # Khởi động lại
docker logs kafka          # Xem logs
```

### 2. Iceberg ClassNotFoundException

**Triệu chứng:** `java.lang.ClassNotFoundException: org.apache.iceberg.spark.SparkCatalog`

```bash
# Đảm bảo có --packages khi chạy spark-submit
spark-submit \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0 \
  spark_to_iceberg_bronze.py
```

### 3. Windows Hadoop DLL error (exitCode=-1073741515)

**Triệu chứng:** `Py4JJavaError: exitCode=-1073741515`

```bash
# Download từ: https://github.com/cdarlint/winutils/tree/master/hadoop-3.3.6/bin
# Copy hadoop.dll vào: C:\spark\hadoop\bin\
# Cài Visual C++ Runtime:
winget install Microsoft.VCRedist.2010.x64
```

### 4. Query không trả về dữ liệu

**Triệu chứng:** `Query returns: 0 rows`

```bash
# Kiểm tra Producer Terminal 1 có đang gửi data
# Kiểm tra Spark Terminal 2 có đang chạy
# Đợi thêm 1-2 phút cho data được commit

# Kiểm tra thư mục Iceberg:
ls D:/Bigdata/iceberg-warehouse/stock_db/stock_bronze/data/
```

---

###Schema của bronze data

```bash
bronze_schema = StructType([
    # Thông tin cổ phiếu
    StructField("symbol", StringType(), False),           # Mã cổ phiếu (VD: AAPL, GOOGL)

    # Giá cổ phiếu
    StructField("open", DoubleType(), True),              # Giá mở cửa
    StructField("high", DoubleType(), True),              # Giá cao nhất
    StructField("low", DoubleType(), True),               # Giá thấp nhất
    StructField("close", DoubleType(), True),             # Giá đóng cửa
    StructField("adj_close", DoubleType(), True),         # Giá đóng cửa điều chỉnh

    # Khối lượng giao dịch
    StructField("volume", LongType(), True),              # Khối lượng giao dịch

    # Thời gian
    StructField("timestamp", TimestampType(), False),     # Thời điểm lấy dữ liệu
    StructField("date", StringType(), True),              # Ngày giao dịch (YYYY-MM-DD)

    # Metadata
    StructField("ingestion_time", TimestampType(), False) # Thời gian nhập vào hệ thống
])

```

_Last updated: 2024-01-15_
_Version: 1.0 - Complete End-to-End Pipeline_
