# Bigdata Stock Market Analysis

Real-time stock data pipeline with live technical analysis dashboard using Kafka, Spark Streaming, Apache Iceberg, MinIO, and Streamlit.

## ⚡ Quick Start

**Option 1: Automated Start (Windows)**

```bash
# One-click startup (opens 5 terminal windows)
start_pipeline.bat
```

**Option 2: Manual Start**

```bash
# 1. Start infrastructure
docker compose up -d

# 2. Run in separate terminals:
cd raw_data_bronze && python spark_to_iceberg_bronze.py
cd processed_data_silver && python bronze_to_silver.py
cd processed_data_gold && python silver_to_gold_streaming.py
cd processed_data_gold && streamlit run dashboard.py  # Opens at http://localhost:8501
```

**Check Pipeline Status**

```bash
python check_pipeline_status.py
```

📖 **Detailed Guide**: See [QUICKSTART_DASHBOARD.md](QUICKSTART_DASHBOARD.md)

---

## 🎯 What You Get

- **📊 Live Dashboard** at http://localhost:8501 with:

  - Real-time candlestick charts
  - Technical indicators (SMA, RSI, MACD, Bollinger Bands)
  - Trading signals (BUY/SELL/HOLD)
  - Sector performance analysis
  - Auto-refresh every 5-60 seconds

- **🔄 Real-time Streaming Pipeline**:

  - Bronze Layer: Raw data ingestion
  - Silver Layer: Data quality & validation
  - Gold Layer: Technical indicators & signals

- **📈 50+ Stock Symbols** tracked in real-time
- **⚡ End-to-end latency**: 30-90 seconds
- **🎨 Beautiful UI** with Streamlit and Plotly

📚 **Full Feature List**: See [FEATURES.md](FEATURES.md)

---

## Architecture

```
Yahoo Finance → Kafka → Bronze Layer → Silver Layer → Gold Layer → Dashboard
     API              (Raw Data)    (Cleansed)    (Analytics)   (Streamlit)
                          ↓              ↓             ↓
                      Iceberg        Iceberg       Iceberg
                       MinIO          MinIO         MinIO
```

### Data Layers (Medallion Architecture)

- **Bronze Layer** 🥉: Raw, unprocessed data from sources (append-only)
- **Silver Layer** 🥈: Cleansed, validated, deduplicated data (quality-checked)
- **Gold Layer** 🥇: Aggregated analytics with technical indicators (business-ready)
- **Dashboard** 📊: Real-time Streamlit UI with live charts and signals

## Tech Stack

- **Kafka (KRaft mode)**: Message streaming (no ZooKeeper)
- **Apache Spark**: Stream processing & technical indicators
- **Apache Iceberg**: Data lakehouse table format with time-travel
- **MinIO**: S3-compatible object storage
- **Streamlit**: Real-time analytics dashboard
- **Plotly**: Interactive charts and visualizations
- **Python**: Data ingestion, processing, and analytics

## Quick Start

### 1. Start infrastructure (Kafka + MinIO) with Docker Compose

```bash
docker compose up -d
```

This starts only the infrastructure:

- **MinIO** on ports 9000 (API) and 9001 (Console)
- **Kafka** on port 9092 (KRaft mode, no ZooKeeper)
- **Bucket init** via `minio-init`

### 2. Access Services

- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Kafka**: localhost:9092

### 3. Create Kafka Topic

```bash
docker exec kafka kafka-topics --create \
  --if-not-exists \
  --bootstrap-server localhost:9092 \
  --topic stock_ticks \
  --partitions 1 \
  --replication-factor 1
```

### 4. Verify Data in MinIO

1. Open MinIO Console at http://localhost:9001
2. Login with `minioadmin` / `minioadmin`
3. Check the `warehouse` bucket for Iceberg data

### 5. Run the pipeline locally (no containers for code)

1. Copy env vars and install deps

```bash
cp .env.example .env
cd raw_data_bronze
pip install -r requirements.txt
```

2. Export env vars

```bash
# PowerShell
$env:KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
$env:KAFKA_TOPIC="stock_ticks"
$env:MINIO_ENDPOINT="http://localhost:9000"
$env:MINIO_ACCESS_KEY="minioadmin"
$env:MINIO_SECRET_KEY="minioadmin"
$env:ICEBERG_WAREHOUSE="s3a://warehouse"

# Optional: checkpoint dir
$env:CHECKPOINT_LOCATION="./checkpoints/iceberg_bronze"
```

3. Run producer locally

```bash
cd raw_data_bronze
python yahoo_to_kafka.py
```

4. Run Spark streaming locally (new terminal)

```bash
cd raw_data_bronze
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

5. Query Iceberg locally (new terminal)

```bash
cd raw_data_bronze
spark-submit \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.367 \
  query_iceberg_bronze.py
```

## Project Structure

```
.
├── docker-compose.yml              # Service orchestration
├── docker/
│   ├── producer/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── spark/
│       └── Dockerfile
├── raw_data_bronze/
│   ├── yahoo_to_kafka.py          # Producer: Yahoo Finance → Kafka
│   ├── kafka_to_spark.py          # Test: Kafka → Spark console
│   ├── spark_to_iceberg_bronze.py # Main: Spark → Iceberg → MinIO
│   ├── query_iceberg_bronze.py    # Query Iceberg tables
│   └── requirements.txt
├── processed_data_silver/
│   ├── bronze_to_silver.py        # Silver: Data quality & cleansing
│   ├── query_iceberg_silver.py    # Query Silver layer
├── processed_data_gold/
│   ├── silver_to_gold_streaming.py # Gold: Technical indicators & signals
│   ├── dashboard.py               # Streamlit real-time dashboard
│   ├── query_iceberg_gold.py      # Query Gold layer
│   ├── requirements.txt
│   └── README.md                  # Gold layer documentation
│   ├── requirements.txt
│   └── README.md                  # Silver layer documentation
└── .env.example                    # Environment variables template
```

## Development

Develop and run everything locally; Docker is used only for Kafka/MinIO. Follow the Quick Start section to set env vars, install deps, and run `yahoo_to_kafka.py` and `spark_to_iceberg_bronze.py` directly from your machine.

## Key Changes from Original Setup

✅ **Removed ZooKeeper** - Kafka now runs in KRaft mode  
✅ **Removed Hadoop dependency** - Using MinIO S3 instead of local HDFS  
✅ **Docker for infra only** - Kafka/MinIO in containers; code runs locally  
✅ **Spark on host** - Use your local Spark install (3.5.7)  
✅ **S3-compatible storage** - Iceberg data stored in MinIO  
✅ **Environment variables** - Easy configuration for Docker and local dev

## Troubleshooting

### View logs

```bash
# Infrastructure services
docker compose logs -f

# Kafka only
docker compose logs -f kafka
```

### Restart services

```bash
docker compose restart kafka
docker compose restart minio
```

### Clean up and restart

```bash
docker compose down -v
docker compose up -d
```

### Initialize MinIO bucket manually

If the warehouse bucket doesn't exist:

```bash
docker run --rm --network bigdata-stock-market-analysis_default \
  --entrypoint sh minio/mc -c "\
  mc alias set myminio http://minio:9000 minioadmin minioadmin && \
  mc mb myminio/warehouse --ignore-existing"
```

## Data Flow

### Complete Real-time Streaming Pipeline

```
┌─────────────────┐
│  Yahoo Finance  │
│      API        │
└────────┬────────┘
         │ 30s interval
         ▼
┌─────────────────┐
│     Kafka       │
│  stock_ticks    │
└────────┬────────┘
         │ streaming
         ▼
┌─────────────────────────────────────────────────────┐
│              Bronze Layer (Raw Data)                │
│  • Append-only ingestion                            │
│  • No transformations                               │
│  • Time-travel enabled                              │
└────────┬────────────────────────────────────────────┘
         │ streaming
         ▼
┌─────────────────────────────────────────────────────┐
│           Silver Layer (Data Quality)               │
│  • Price & volume validation                        │
│  • Deduplication                                    │
│  • Anomaly detection                                │
│  • Missing value imputation                         │
└────────┬────────────────────────────────────────────┘
         │ streaming (15s batches)
         ▼
┌─────────────────────────────────────────────────────┐
│        Gold Layer (Technical Analytics)             │
│  • Moving Averages (SMA 5, 20, 50)                  │
│  • RSI (Relative Strength Index)                    │
│  • MACD & Signal Line                               │
│  • Bollinger Bands                                  │
│  • Trading Signals (Buy/Sell/Hold)                  │
└────────┬────────────────────────────────────────────┘
         │ real-time query
         ▼
┌─────────────────────────────────────────────────────┐
│         Streamlit Dashboard (Live UI)               │
│  • Real-time candlestick charts                     │
│  • Technical indicator overlays                     │
│  • Trading signals table                            │
│  • Sector performance                               │
│  • Auto-refresh (5-60s)                             │
└─────────────────────────────────────────────────────┘
```

### Running the Complete Pipeline

**Terminal 1: Bronze Layer (Raw Ingestion)**

```bash
cd raw_data_bronze
python spark_to_iceberg_bronze.py
```

**Terminal 2: Silver Layer (Data Quality)**

```bash
cd processed_data_silver
python bronze_to_silver.py
```

**Terminal 3: Gold Layer (Technical Indicators)** 🆕

```bash
cd processed_data_gold
python silver_to_gold_streaming.py
```

**Terminal 4: Real-time Dashboard** 🆕

```bash
cd processed_data_gold
streamlit run dashboard.py
# Opens at http://localhost:8501
```

**Terminal 5: Producer (if not running)**

```bash
cd raw_data_bronze
python yahoo_to_kafka.py
```

### Dashboard Features 📊

The Streamlit dashboard provides:

- **📈 Live Market Overview**: Total stocks, Buy/Sell/Hold signals, Average RSI
- **🎯 Trading Signals Table**: Color-coded recommendations with price changes
- **📊 Technical Charts**: Interactive candlestick charts with:
  - Bollinger Bands overlay
  - Moving Averages (SMA 5, 20, 50)
  - Volume bars
  - RSI indicator with oversold/overbought levels
- **📉 MACD Charts**: MACD line, signal line, and histogram
- **🏢 Sector Performance**: Aggregated metrics by sector
- **🔄 Auto-refresh**: Configurable refresh interval (5-60 seconds)
- **🎛️ Filters**: Select specific symbols and sectors

See detailed documentation:

- [Silver Layer README](processed_data_silver/README.md)
- [Gold Layer README](processed_data_gold/README.md)

## Query Data

**Bronze Layer**:

```bash
cd raw_data_bronze
python query_iceberg_bronze.py
```

**Silver Layer**:

```bash
cd processed_data_silver
python query_iceberg_silver.py
```

**Gold Layer** 🆕:

```bash
cd processed_data_gold
python query_iceberg_gold.py
```

## Stop Services

```bash
docker compose down

# To also remove volumes (data will be lost)
docker compose down -v
```
