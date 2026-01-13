# 📁 Project Files Summary

Complete reference guide for all files in the project.

## 🗂️ Directory Structure

```
bigdata-stock-market-analysis/
│
├── 📋 Documentation Files
│   ├── README.md                    # Main project documentation
│   ├── QUICKSTART_DASHBOARD.md      # Quick start guide for dashboard
│   ├── FEATURES.md                  # Complete feature list
│   ├── DASHBOARD_GUIDE.md           # Dashboard visual guide
│   ├── QUICKSTART.md                # Original quick start
│   ├── TROUBLESHOOTING.md           # Common issues and solutions
│   └── MIGRATION.md                 # Migration notes
│
├── 🚀 Startup Scripts
│   ├── start_pipeline.bat           # Windows batch script (auto-start)
│   ├── start_pipeline.sh            # Linux/Mac bash script
│   └── check_pipeline_status.py    # Pipeline health check utility
│
├── 🐳 Docker Configuration
│   ├── docker-compose.yml           # Kafka + MinIO services
│   ├── .env.example                 # Environment variables template
│   └── .env                         # Local environment config (gitignored)
│
├── 🥉 Bronze Layer (Raw Data)
│   └── raw_data_bronze/
│       ├── yahoo_to_kafka.py        # Producer: Yahoo Finance → Kafka
│       ├── kafka_to_spark.py        # Test: Kafka → Spark console
│       ├── spark_to_iceberg_bronze.py  # Main: Kafka → Iceberg
│       ├── query_iceberg_bronze.py  # Query Bronze table
│       ├── requirements.txt         # Python dependencies
│       └── EXECUTION_PLAN.md        # Bronze layer detailed plan
│
├── 🥈 Silver Layer (Data Quality)
│   └── processed_data_silver/
│       ├── bronze_to_silver.py      # Data quality & cleansing
│       ├── query_iceberg_silver.py  # Query Silver table
│       ├── requirements.txt         # Python dependencies
│       └── README.md                # Silver layer documentation
│
├── 🥇 Gold Layer (Analytics)
│   └── processed_data_gold/
│       ├── silver_to_gold_streaming.py  # Technical indicators
│       ├── dashboard.py             # Streamlit real-time dashboard ⭐
│       ├── query_iceberg_gold.py    # Query Gold table
│       ├── requirements.txt         # Python dependencies (includes Streamlit)
│       └── README.md                # Gold layer documentation
│
└── 🔧 Configuration & Utilities
    └── .gitignore                   # Git ignore rules
```

## 📄 File Descriptions

### Core Documentation

#### README.md

**Purpose**: Main project documentation with architecture overview
**Contents**:

- Quick start instructions
- Architecture diagram
- Tech stack
- Complete pipeline setup
- Data flow visualization

#### QUICKSTART_DASHBOARD.md ⭐

**Purpose**: Step-by-step guide to get the full pipeline running
**Contents**:

- 5-step setup process
- Environment variable configuration
- Running all 5 components
- Dashboard usage guide
- Troubleshooting tips

#### FEATURES.md

**Purpose**: Comprehensive feature list and capabilities
**Contents**:

- Technical indicators explained
- Trading signals documentation
- Architecture highlights
- Scalability information
- Use cases and learning paths

#### DASHBOARD_GUIDE.md

**Purpose**: Visual guide to dashboard UI
**Contents**:

- Screenshot representations (ASCII art)
- Dashboard sections explained
- Interactive features
- Performance metrics
- Mobile responsiveness

### Startup Utilities

#### start_pipeline.bat (Windows)

**Purpose**: One-click startup for all components
**How it works**:

1. Checks Docker is running
2. Starts Kafka + MinIO
3. Creates Kafka topic
4. Opens 5 terminal windows:
   - Producer
   - Bronze layer
   - Silver layer
   - Gold layer
   - Dashboard (Streamlit)

**Usage**: `start_pipeline.bat`

#### start_pipeline.sh (Linux/Mac)

**Purpose**: Shell script for Unix-based systems
**How it works**:

- Same as .bat but for bash
- Provides terminal commands to run manually

**Usage**: `bash start_pipeline.sh`

#### check_pipeline_status.py ⭐

**Purpose**: Health check for all pipeline layers
**What it checks**:

- Bronze table: Record count, latest timestamp
- Silver table: Quality metrics, anomalies
- Gold table: Signal distribution, recommendations
- Overall pipeline flow status

**Usage**: `python check_pipeline_status.py`

**Output Example**:

```
🥉 BRONZE LAYER (Raw Data)
  ✅ Status: ACTIVE
  📊 Total Records: 1,250
  🕐 Latest Record: 2026-01-13 14:30:00

🥈 SILVER LAYER (Cleansed Data)
  ✅ Status: ACTIVE
  📊 Total Records: 1,248
  ✔️  Valid Prices: 1,246 (99.8%)

🥇 GOLD LAYER (Analytics & Indicators)
  ✅ Status: ACTIVE
  📊 Total Records: 1,200
  🎯 Trading Signals:
     🟢 STRONG BUY: 12
     🟢 BUY: 15
     🟡 HOLD: 30
     🔴 SELL: 8
     🔴 STRONG SELL: 5
```

### Bronze Layer Files

#### yahoo_to_kafka.py

**Purpose**: Fetch stock data from Yahoo Finance and publish to Kafka
**Features**:

- 50+ stock symbols across sectors
- 30-second fetch interval
- JSON message format
- Error handling and retries

**Key Configuration**:

```python
SYMBOLS = ["AAPL", "GOOGL", "MSFT", ...]
FETCH_INTERVAL = 30  # seconds
```

#### spark_to_iceberg_bronze.py ⭐

**Purpose**: Stream data from Kafka to Iceberg Bronze table
**Features**:

- Kafka consumer with Spark Streaming
- Schema validation
- Iceberg writes with MinIO backend
- Checkpoint management

**Environment Variables Required**:

- `KAFKA_BOOTSTRAP_SERVERS`
- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `ICEBERG_WAREHOUSE`

#### query_iceberg_bronze.py

**Purpose**: Query and display Bronze layer data
**Shows**:

- Total record count
- Sample records
- Latest timestamps
- Data by symbol

### Silver Layer Files

#### bronze_to_silver.py ⭐

**Purpose**: Real-time data quality processing
**Features**:

- Price validation (OHLC rules)
- Volume validation
- Deduplication (symbol, timestamp)
- Anomaly detection (50% price, 10x volume)
- Missing value imputation
- Quality metrics per batch

**Processing Interval**: 10 seconds

**Quality Checks**:

```python
- is_valid_price: OHLC rules, positivity
- is_valid_volume: Non-negative
- is_complete_record: Required fields present
- has_anomaly: Unusual movements detected
- *_imputed flags: Missing values filled
```

#### query_iceberg_silver.py

**Purpose**: Query Silver layer with quality statistics
**Shows**:

- Total records and quality %
- Per-symbol statistics
- Anomalies detected
- Imputed records
- Data quality dashboard

### Gold Layer Files

#### silver_to_gold_streaming.py ⭐

**Purpose**: Calculate technical indicators in real-time
**Features**:

- Moving Averages (SMA 5, 20, 50, EMA 12)
- RSI (14-period Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands (20-period, 2 standard deviations)
- Volume analysis
- Trading signal generation
- Recommendation engine (STRONG BUY → STRONG SELL)

**Processing Interval**: 15 seconds

**Technical Indicators Calculated**:
| Indicator | Formula | Use Case |
|-----------|---------|----------|
| SMA | Average(Close, N) | Trend identification |
| RSI | 100 - (100/(1+RS)) | Overbought/oversold |
| MACD | EMA(12) - EMA(26) | Trend momentum |
| BB | SMA(20) ± 2σ | Volatility, breakouts |

#### dashboard.py ⭐⭐⭐

**Purpose**: Real-time Streamlit dashboard
**Features**:

- Live market overview (stocks, signals, RSI)
- Trading signals table with color coding
- Interactive candlestick charts
- Technical indicator overlays
- MACD charts
- Sector performance analysis
- Auto-refresh (5-60 seconds)
- Symbol and sector filters
- Mobile responsive

**Key Components**:

```python
1. get_spark_session(): Initialize Spark (cached)
2. load_gold_data(): Load records from Gold table
3. load_latest_by_symbol(): Get latest per symbol
4. create_candlestick_chart(): Build price charts
5. create_macd_chart(): Build MACD charts
6. Main loop: Auto-refresh logic
```

**URL**: http://localhost:8501

#### query_iceberg_gold.py

**Purpose**: Query Gold layer with analytics
**Shows**:

- Latest signals per symbol
- Signal distribution (buy/sell/hold counts)
- Buy/sell signal lists
- Golden/death cross events
- RSI extremes (oversold/overbought)
- Sector performance
- Top/bottom performers

## 📊 Data Tables

### Bronze Table: stock_bronze

```sql
Columns:
- symbol: Stock ticker (STRING)
- sector: Industry sector (STRING)
- open, high, low, close: OHLC prices (DOUBLE)
- volume: Trading volume (LONG)
- event_time: Event timestamp (STRING)
- source: Data source (STRING)
- ingest_time: Ingestion timestamp (TIMESTAMP)

Partitioning: None (append-only)
Purpose: Raw data lake
```

### Silver Table: stock_silver

```sql
Columns:
- [All Bronze columns]
- processed_time: Processing timestamp (TIMESTAMP)
- is_valid_price: Price validation flag (BOOLEAN)
- is_valid_volume: Volume validation flag (BOOLEAN)
- is_complete_record: Completeness flag (BOOLEAN)
- has_anomaly: Anomaly detection flag (BOOLEAN)
- open_imputed, high_imputed, low_imputed, close_imputed (BOOLEAN)

Partitioning: days(processed_time)
Purpose: Clean, validated data
```

### Gold Table: stock_gold_realtime

```sql
Columns:
- [Core price data: symbol, sector, OHLC, volume]
- sma_5, sma_20, sma_50, ema_12: Moving averages (DOUBLE)
- price_change, price_change_pct: Price metrics (DOUBLE)
- rsi_14: Relative Strength Index (DOUBLE)
- macd, macd_signal, macd_histogram: MACD values (DOUBLE)
- bb_upper, bb_middle, bb_lower, bb_width: Bollinger Bands (DOUBLE)
- volume_sma_20, volume_ratio: Volume metrics (DOUBLE)
- volatility_20: Volatility measure (DOUBLE)
- golden_cross, death_cross, rsi_oversold, rsi_overbought,
  macd_bullish, macd_bearish, bb_squeeze: Signal flags (BOOLEAN)
- signal_score: Composite score (INT)
- recommendation: Trading action (STRING)
- processed_time: Processing timestamp (TIMESTAMP)

Partitioning: hours(processed_time)
Purpose: Analytics-ready with indicators
```

## 🔄 Data Flow Diagram

```
[yahoo_to_kafka.py]
       ↓ (30s interval)
   [Kafka Topic]
       ↓ (streaming)
[spark_to_iceberg_bronze.py]
       ↓
[stock_bronze table] ← [query_iceberg_bronze.py]
       ↓ (streaming)
[bronze_to_silver.py]
       ↓ (10s batches)
[stock_silver table] ← [query_iceberg_silver.py]
       ↓ (streaming)
[silver_to_gold_streaming.py]
       ↓ (15s batches)
[stock_gold_realtime] ← [query_iceberg_gold.py]
       ↓ (real-time query)
    [dashboard.py] ← User views at http://localhost:8501
```

## 🎯 Key File for Each Task

| Task                  | File to Use                                   |
| --------------------- | --------------------------------------------- |
| Start everything      | `start_pipeline.bat` or manual terminal setup |
| Check pipeline health | `check_pipeline_status.py`                    |
| View live dashboard   | `dashboard.py` (streamlit run)                |
| Query Bronze data     | `query_iceberg_bronze.py`                     |
| Query Silver data     | `query_iceberg_silver.py`                     |
| Query Gold data       | `query_iceberg_gold.py`                       |
| Modify stock symbols  | `yahoo_to_kafka.py`                           |
| Adjust indicators     | `silver_to_gold_streaming.py`                 |
| Customize dashboard   | `dashboard.py`                                |
| Troubleshoot          | `TROUBLESHOOTING.md`                          |

## 📦 Dependencies

### Bronze Layer

```
pyspark==3.5.7
kafka-python==2.0.2
yfinance==0.2.35
```

### Silver Layer

```
pyspark==3.5.7
```

### Gold Layer

```
pyspark==3.5.7
streamlit==1.30.0
plotly==5.18.0
pandas==2.1.4
```

## 🔧 Configuration Files

### .env.example

Template for environment variables

```bash
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
ICEBERG_WAREHOUSE=s3a://warehouse
```

### docker-compose.yml

Services configuration:

- Kafka (KRaft mode, port 9092)
- MinIO (ports 9000, 9001)
- MinIO init (creates warehouse bucket)

## 📝 Quick Reference

### Most Important Files

1. **dashboard.py** - The star of the show ⭐⭐⭐
2. **silver_to_gold_streaming.py** - Technical indicators engine
3. **spark_to_iceberg_bronze.py** - Data ingestion
4. **bronze_to_silver.py** - Data quality
5. **check_pipeline_status.py** - Health check utility

### Documentation Hierarchy

```
README.md (start here)
    ↓
QUICKSTART_DASHBOARD.md (setup guide)
    ↓
FEATURES.md (what you get)
    ↓
DASHBOARD_GUIDE.md (visual guide)
    ↓
Layer-specific READMEs (deep dive)
```

---

**Need help?**

- Check `TROUBLESHOOTING.md`
- Run `python check_pipeline_status.py`
- Review layer-specific `README.md` files
