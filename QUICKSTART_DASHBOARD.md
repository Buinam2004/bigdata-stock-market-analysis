# 🚀 Quick Start Guide - Real-time Stock Analytics

Complete setup guide for the real-time streaming pipeline with live dashboard.

## Prerequisites

- **Docker Desktop** (for Kafka & MinIO)
- **Python 3.10+** with pip
- **Java 11 or 21** (for Spark)
- **Apache Spark 3.5.7** installed locally

## 🎯 Complete Setup (5 Steps)

### Step 1: Start Infrastructure

```bash
# Start Kafka and MinIO
docker compose up -d

# Verify services are running
docker compose ps
```

Services will be available at:

- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Kafka**: localhost:9092

### Step 2: Create Kafka Topic

```bash
docker exec kafka kafka-topics --create \
  --if-not-exists \
  --bootstrap-server localhost:9092 \
  --topic stock_ticks \
  --partitions 1 \
  --replication-factor 1
```

### Step 3: Install Python Dependencies

```bash
# Bronze layer
cd raw_data_bronze
pip install -r requirements.txt

# Silver layer
cd ../processed_data_silver
pip install -r requirements.txt

# Gold layer
cd ../processed_data_gold
pip install -r requirements.txt

cd ..
```

### Step 4: Set Environment Variables

**PowerShell**:

```powershell
$env:KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
$env:MINIO_ENDPOINT="http://localhost:9000"
$env:MINIO_ACCESS_KEY="minioadmin"
$env:MINIO_SECRET_KEY="minioadmin"
$env:ICEBERG_WAREHOUSE="s3a://warehouse"
```

**Bash/WSL**:

```bash
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export MINIO_ENDPOINT="http://localhost:9000"
export MINIO_ACCESS_KEY="minioadmin"
export MINIO_SECRET_KEY="minioadmin"
export ICEBERG_WAREHOUSE="s3a://warehouse"
```

### Step 5: Run the Pipeline

Open **5 terminals** and run each command:

**Terminal 1: Data Producer**

```bash
cd raw_data_bronze
python yahoo_to_kafka.py
```

✅ Fetches stock data every 30 seconds

**Terminal 2: Bronze Layer**

```bash
cd raw_data_bronze
python spark_to_iceberg_bronze.py
```

✅ Ingests raw data from Kafka → Iceberg

**Terminal 3: Silver Layer**

```bash
cd processed_data_silver
python bronze_to_silver.py
```

✅ Cleanses and validates data with quality checks

**Terminal 4: Gold Layer**

```bash
cd processed_data_gold
python silver_to_gold_streaming.py
```

✅ Calculates technical indicators and trading signals

**Terminal 5: Streamlit Dashboard**

```bash
cd processed_data_gold
streamlit run dashboard.py
```

✅ Opens dashboard at http://localhost:8501

## 📊 Using the Dashboard

1. **Wait 1-2 minutes** for data to flow through all layers
2. **Select symbols** from the sidebar (e.g., AAPL, GOOGL, MSFT)
3. **Enable auto-refresh** for live updates
4. **Adjust refresh interval** (5-60 seconds)
5. **Explore tabs** to see detailed charts per symbol

### Dashboard Sections

- **Market Overview**: Total stocks, signal counts, average RSI
- **Trading Signals**: Color-coded recommendations table
- **Technical Analysis**:
  - Candlestick charts with Bollinger Bands
  - Moving averages (SMA 5, 20, 50)
  - Volume bars
  - RSI indicator
  - MACD charts
- **Sector Performance**: Aggregated metrics by sector

## 🔍 Verify Data Flow

Check each layer to ensure data is flowing:

```bash
# Check Bronze (raw data)
cd raw_data_bronze
python query_iceberg_bronze.py

# Check Silver (cleansed data)
cd ../processed_data_silver
python query_iceberg_silver.py

# Check Gold (analytics data)
cd ../processed_data_gold
python query_iceberg_gold.py
```

## 📈 What You'll See

### Bronze Layer Output

```
Total records in Bronze: 1250
symbol  sector      close   volume      event_time
AAPL    Technology  175.20  52000000    2026-01-13 10:30:00
```

### Silver Layer Output

```
Data Quality Statistics:
Valid Prices:    1248 (99.8%)
Anomalies:       3 (0.2%)
Imputed Values:  0
```

### Gold Layer Output

```
Trading Signals:
symbol  close   rsi_14  signal_score  recommendation
AAPL    175.20  65.5    2             STRONG BUY
GOOGL   142.30  45.2    -1            SELL
MSFT    380.50  55.0    0             HOLD
```

### Dashboard

Live charts updating every 5-60 seconds with:

- Real-time price movements
- Technical indicator overlays
- Buy/Sell/Hold signals
- Sector performance

## ⚡ Performance Tips

### For Faster Processing

```python
# In each streaming script, reduce batch interval:
.trigger(processingTime="5 seconds")  # default is 10-15s
```

### For Lower Resource Usage

```python
# Reduce Spark memory:
.config("spark.driver.memory", "1g")
.config("spark.executor.memory", "1g")
```

### For Dashboard Speed

```python
# In dashboard.py, reduce data load:
df_all = load_gold_data(limit=1000)  # default is 5000
refresh_interval = st.slider(..., 30)  # increase refresh interval
```

## 🛑 Stopping the Pipeline

```bash
# Stop all Python processes (Ctrl+C in each terminal)

# Stop Docker services
docker compose down

# To remove all data:
docker compose down -v
```

## 🐛 Troubleshooting

### Issue: No data in dashboard

**Solution**:

1. Check all 4 processors are running (Producer, Bronze, Silver, Gold)
2. Wait 2-3 minutes for data to propagate
3. Check logs for errors

### Issue: Dashboard shows "Waiting for data"

**Solution**:

```bash
# Verify Gold table has data
cd processed_data_gold
python query_iceberg_gold.py

# If empty, check Silver layer
cd ../processed_data_silver
python query_iceberg_silver.py
```

### Issue: "Connection refused" errors

**Solution**:

```bash
# Check Docker services
docker compose ps

# Restart if needed
docker compose restart kafka
docker compose restart minio
```

### Issue: Out of memory

**Solution**:

```python
# Reduce Spark memory in each script:
.config("spark.driver.memory", "1g")
.config("spark.sql.shuffle.partitions", "2")
```

### Issue: Slow dashboard

**Solution**:

```python
# In dashboard.py:
df_all = load_gold_data(limit=500)  # reduce data
auto_refresh = False  # disable auto-refresh temporarily
```

## 📚 Next Steps

1. **Customize Stocks**: Edit `yahoo_to_kafka.py` to add more symbols
2. **Tune Indicators**: Modify SMA periods in `silver_to_gold_streaming.py`
3. **Add Alerts**: Integrate email/SMS for strong buy/sell signals
4. **Export Data**: Query Gold layer and export to CSV for analysis
5. **Backtest Strategies**: Use historical data to test trading strategies

## 🎓 Learning Resources

- [Apache Iceberg](https://iceberg.apache.org/)
- [Spark Structured Streaming](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Streamlit Docs](https://docs.streamlit.io/)
- [Technical Analysis](https://www.investopedia.com/terms/t/technicalindicator.asp)

## 📝 Summary

You now have a complete real-time stock analytics pipeline:

- ✅ Data ingestion from Yahoo Finance
- ✅ 3-layer Medallion architecture (Bronze/Silver/Gold)
- ✅ Real-time technical indicators
- ✅ Trading signal generation
- ✅ Live Streamlit dashboard
- ✅ Interactive charts and metrics

**Enjoy your real-time stock analytics platform! 📈🚀**
