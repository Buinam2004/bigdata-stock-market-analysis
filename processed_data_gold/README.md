# Gold Layer - Real-time Technical Indicators & Analytics

The Gold layer processes clean data from the Silver layer, calculating technical indicators in real-time and generating trading signals for live analytics and visualization.

## Overview

**Purpose**: Calculate technical indicators, generate trading signals, and provide real-time analytics-ready data.

**Data Flow**:

```
Silver Table (stock_silver) → Technical Calculations → Gold Table (stock_gold_realtime) → Streamlit Dashboard
```

## Architecture

```
┌─────────────┐
│   Silver    │
│  (Cleaned)  │
└──────┬──────┘
       │ Streaming
       ▼
┌─────────────────────────────────────┐
│  Gold Layer Processing              │
│  • Moving Averages (SMA 5,20,50)    │
│  • RSI (14-period)                  │
│  • MACD & Signal Line               │
│  • Bollinger Bands                  │
│  • Volume Analysis                  │
│  • Trading Signals                  │
└──────┬──────────────────────────────┘
       │
       ▼
┌──────────────┐       ┌────────────────┐
│  Gold Table  │ ───── │   Streamlit    │
│ (Indicators) │       │   Dashboard    │
└──────────────┘       └────────────────┘
```

## Features

### 1. Technical Indicators 📊

#### Moving Averages

- **SMA 5**: 5-period Simple Moving Average
- **SMA 20**: 20-period Simple Moving Average
- **SMA 50**: 50-period Simple Moving Average
- **EMA 12**: 12-period Exponential Moving Average

#### Momentum Indicators

- **RSI (14)**: Relative Strength Index
  - Oversold: < 30
  - Overbought: > 70

#### Trend Indicators

- **MACD**: Moving Average Convergence Divergence
  - MACD Line (EMA 12 - EMA 26)
  - Signal Line (9-period EMA of MACD)
  - Histogram (MACD - Signal)

#### Volatility Indicators

- **Bollinger Bands**:
  - Upper Band: SMA 20 + (2 × StdDev)
  - Middle Band: SMA 20
  - Lower Band: SMA 20 - (2 × StdDev)
  - BB Width: Upper - Lower

### 2. Volume Analysis 📦

- **Volume SMA 20**: 20-period average volume
- **Volume Ratio**: Current volume / 20-period average
- **Volatility**: 20-period standard deviation of close price

### 3. Trading Signals 🎯

#### Signal Types

- **Golden Cross** 🟢: SMA 5 crosses above SMA 20 (Bullish)
- **Death Cross** 🔴: SMA 5 crosses below SMA 20 (Bearish)
- **RSI Oversold** 🟢: RSI < 30 (Potential buy)
- **RSI Overbought** 🔴: RSI > 70 (Potential sell)
- **MACD Bullish** 🟢: MACD > Signal Line
- **MACD Bearish** 🔴: MACD < Signal Line
- **BB Squeeze** ⚠️: Low volatility (potential breakout)

#### Recommendation System

```python
Signal Score =
  + 2 if Golden Cross
  - 2 if Death Cross
  + 1 if RSI Oversold
  - 1 if RSI Overbought
  + 1 if MACD Bullish
  - 1 if MACD Bearish

Recommendation:
  Score >= 2  → STRONG BUY
  Score == 1  → BUY
  Score == 0  → HOLD
  Score == -1 → SELL
  Score <= -2 → STRONG SELL
```

## Gold Table Schema

```sql
CREATE TABLE stock_gold_realtime (
    -- Core Data
    symbol STRING,
    sector STRING,
    event_time TIMESTAMP,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume LONG,

    -- Moving Averages
    sma_5 DOUBLE,
    sma_20 DOUBLE,
    sma_50 DOUBLE,
    ema_12 DOUBLE,

    -- Price Metrics
    price_change DOUBLE,
    price_change_pct DOUBLE,

    -- RSI
    rsi_14 DOUBLE,

    -- MACD
    macd DOUBLE,
    macd_signal DOUBLE,
    macd_histogram DOUBLE,

    -- Bollinger Bands
    bb_upper DOUBLE,
    bb_middle DOUBLE,
    bb_lower DOUBLE,
    bb_width DOUBLE,

    -- Volume
    volume_sma_20 DOUBLE,
    volume_ratio DOUBLE,

    -- Volatility
    volatility_20 DOUBLE,

    -- Trading Signals
    golden_cross BOOLEAN,
    death_cross BOOLEAN,
    rsi_oversold BOOLEAN,
    rsi_overbought BOOLEAN,
    macd_bullish BOOLEAN,
    macd_bearish BOOLEAN,
    bb_squeeze BOOLEAN,

    -- Recommendations
    signal_score INT,
    recommendation STRING,

    -- Metadata
    processed_time TIMESTAMP
) USING iceberg
PARTITIONED BY (hours(processed_time))
```

## Scripts

### 1. `silver_to_gold_streaming.py`

Real-time streaming processor that reads from Silver and calculates all technical indicators.

**Features**:

- Streaming processing with 15-second batches
- Calculates all technical indicators per batch
- Generates trading signals automatically
- Batch-level analytics and monitoring
- Fault-tolerant with checkpoints

**Environment Variables**:

```bash
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
ICEBERG_WAREHOUSE=s3a://warehouse
CHECKPOINT_LOCATION_GOLD=./checkpoints/iceberg_gold
```

### 2. `dashboard.py`

Real-time Streamlit dashboard for live market analytics and visualization.

**Features**:

- 📊 Live market overview with key metrics
- 🎯 Active trading signals table
- 📈 Interactive candlestick charts with indicators
- 📉 MACD charts
- 🏢 Sector performance analysis
- 🔄 Auto-refresh capability
- 🎨 Beautiful UI with color-coded signals

### 3. `query_iceberg_gold.py`

Query and analyze Gold layer data with comprehensive reports.

**Outputs**:

- Latest trading signals per symbol
- Signal distribution summary
- Buy/Sell signal lists
- Golden/Death cross events
- RSI extremes
- Sector performance
- Top/Bottom performers

## Usage

### Step 1: Start Gold Layer Processing

```bash
# Terminal 1: Gold layer processor
cd processed_data_gold
python silver_to_gold_streaming.py
```

Expected output:

```
================================================================================
GOLD LAYER: Real-time Technical Indicators & Analytics
================================================================================
SparkSession initialized!

================================================================================
[BATCH 1] Processing 250 records
================================================================================
  📊 Calculating Moving Averages...
  📈 Calculating RSI...
  📉 Calculating MACD...
  📊 Calculating Bollinger Bands...
  📦 Calculating Volume Metrics...
  🎯 Generating Trading Signals...

  📊 Batch Analytics:
     Total records:     250
     BUY signals:       45 (18.0%)
     SELL signals:      32 (12.8%)
     HOLD signals:      173 (69.2%)

  🎯 Sample Recommendations:
  +------+-------+------+------+------+------------+----------------+
  |symbol|close  |sma_5 |sma_20|rsi_14|signal_score|recommendation  |
  +------+-------+------+------+------+------------+----------------+
  |AAPL  |175.20 |174.10|172.50|65.5  |2           |STRONG BUY      |
  |GOOGL |142.30 |143.00|144.20|45.2  |-1          |SELL            |
  +------+-------+------+------+------+------------+----------------+

  ✓ Batch 1 completed successfully!
```

### Step 2: Launch Streamlit Dashboard

```bash
# Terminal 2: Streamlit dashboard
cd processed_data_gold
streamlit run dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

### Step 3: Query Gold Data

```bash
cd processed_data_gold
python query_iceberg_gold.py
```

## Dashboard Features

### 📊 Market Overview

- Total stocks being tracked
- Active Buy/Sell/Hold signals
- Average RSI across all stocks
- Real-time updates

### 🎯 Trading Signals

- Color-coded recommendation table
- Price changes and RSI values
- Signal scores
- Last update timestamp

### 📈 Technical Analysis

- Interactive candlestick charts
- Bollinger Bands overlay
- Multiple moving averages (SMA 5, 20, 50)
- Volume bars
- RSI indicator with oversold/overbought levels
- MACD with histogram

### 🏢 Sector Analysis

- Sector performance comparison
- Average price changes by sector
- Volume distribution
- Interactive bar charts

### ⚙️ Dashboard Controls

- Auto-refresh toggle
- Adjustable refresh interval (5-60 seconds)
- Symbol filter
- Sector filter

## Installation

```bash
cd processed_data_gold
pip install -r requirements.txt
```

## Best Practices

### 1. Processing Interval

```python
# Default: 15 seconds
.trigger(processingTime="15 seconds")

# For high-volume: increase interval
.trigger(processingTime="30 seconds")

# For low-latency: decrease interval
.trigger(processingTime="5 seconds")
```

### 2. Dashboard Refresh

- For live trading: 5-10 second refresh
- For analysis: 30-60 second refresh
- Disable auto-refresh when analyzing specific stocks

### 3. Symbol Selection

- Select 3-5 symbols for detailed analysis
- Use sector filters to focus on specific industries
- Monitor high signal_score stocks

### 4. Data Retention

```sql
-- Keep last 7 days of detailed data
CALL local.system.expire_snapshots(
    'stock_db.stock_gold_realtime',
    TIMESTAMP '2026-01-06 00:00:00'
);
```

## Performance Tuning

### Spark Configuration

```python
.config("spark.sql.shuffle.partitions", "4")  # Adjust based on data volume
.config("spark.driver.memory", "2g")
.config("spark.executor.memory", "2g")
```

### Dashboard Optimization

```python
# In dashboard.py, adjust data limits
df_all = load_gold_data(limit=5000)  # Increase for more history
df_latest = load_latest_by_symbol()  # Only latest per symbol
```

### Partitioning Strategy

```sql
PARTITIONED BY (hours(processed_time))
-- Efficient for hourly/daily queries
-- Easy data lifecycle management
```

## Troubleshooting

### Issue: No data in dashboard

```bash
# 1. Check Gold table
python query_iceberg_gold.py

# 2. Verify Silver has data
cd ../processed_data_silver
python query_iceberg_silver.py

# 3. Check Gold processor logs
cd ../processed_data_gold
python silver_to_gold_streaming.py
```

### Issue: Dashboard is slow

```python
# In dashboard.py, reduce data load
df_all = load_gold_data(limit=1000)  # Reduce from 5000

# Increase refresh interval
refresh_interval = st.slider("Refresh interval (seconds)", 10, 120, 30)
```

### Issue: Memory errors

```python
# In silver_to_gold_streaming.py
.config("spark.driver.memory", "4g")
.config("spark.executor.memory", "4g")
```

### Issue: Checkpoints conflict

```bash
# Clear checkpoints
rm -rf ./checkpoints/iceberg_gold
python silver_to_gold_streaming.py
```

## Technical Indicator Formulas

### RSI (Relative Strength Index)

```
RS = Average Gain / Average Loss (14 periods)
RSI = 100 - (100 / (1 + RS))
```

### MACD

```
MACD Line = EMA(12) - EMA(26)
Signal Line = EMA(9) of MACD Line
Histogram = MACD Line - Signal Line
```

### Bollinger Bands

```
Middle Band = SMA(20)
Upper Band = SMA(20) + (2 × StdDev(20))
Lower Band = SMA(20) - (2 × StdDev(20))
```

### Moving Average Crossover

```
Golden Cross: SMA(5) crosses above SMA(20)
Death Cross: SMA(5) crosses below SMA(20)
```

## Integration with Pipeline

### Complete Pipeline Flow

```
1. Producer (yahoo_to_kafka.py)        → Fetches data
2. Bronze (spark_to_iceberg_bronze.py) → Raw ingestion
3. Silver (bronze_to_silver.py)        → Data quality
4. Gold (silver_to_gold_streaming.py)  → Analytics ✓
5. Dashboard (dashboard.py)            → Visualization ✓
```

### Running Complete Pipeline

```bash
# Terminal 1: Bronze layer
cd raw_data_bronze
python spark_to_iceberg_bronze.py

# Terminal 2: Silver layer
cd ../processed_data_silver
python bronze_to_silver.py

# Terminal 3: Gold layer
cd ../processed_data_gold
python silver_to_gold_streaming.py

# Terminal 4: Dashboard
streamlit run dashboard.py

# Terminal 5: Producer (if not running)
cd ../raw_data_bronze
python yahoo_to_kafka.py
```

## Use Cases

1. **Day Trading**: Real-time signals with 5-10 second refresh
2. **Technical Analysis**: Detailed indicator analysis per stock
3. **Portfolio Monitoring**: Track multiple stocks across sectors
4. **Backtesting**: Historical data with technical indicators
5. **Alerts**: Monitor signal_score for actionable trades
6. **Research**: Analyze indicator effectiveness over time

## Next Steps

### Enhancements

1. **ML Models**: Train on historical Gold data for predictions
2. **Alerts**: Email/SMS notifications for strong signals
3. **Backtesting Engine**: Test strategies on historical data
4. **API Layer**: REST API for external consumption
5. **Mobile App**: React Native dashboard
6. **Advanced Indicators**: Ichimoku Cloud, Fibonacci, Elliott Wave

### Production Deployment

1. **Kubernetes**: Deploy Spark jobs on K8s
2. **Monitoring**: Grafana + Prometheus for metrics
3. **Alerting**: PagerDuty integration
4. **Scaling**: Auto-scaling based on data volume
5. **HA**: High availability for dashboard
6. **Auth**: OAuth2 for dashboard access

## References

- [Technical Analysis Library (TA-Lib)](https://ta-lib.org/)
- [Investopedia - Technical Indicators](https://www.investopedia.com/terms/t/technicalindicator.asp)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Plotly Charting](https://plotly.com/python/)
- [Apache Iceberg](https://iceberg.apache.org/)

## Support

For issues or questions:

1. Check logs in Gold processor
2. Verify Silver layer has valid data
3. Review dashboard browser console
4. Check Spark UI (if enabled)
