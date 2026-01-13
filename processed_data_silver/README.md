# Silver Layer - Data Quality & Cleansing

The Silver layer processes raw data from the Bronze layer, applying data quality validations, cleansing, and deduplication to produce analytics-ready data.

## Overview

**Purpose**: Transform raw Bronze data into clean, validated, deduplicated data suitable for analytics.

**Data Flow**:

```
Bronze Table (stock_bronze) → Data Quality Checks → Silver Table (stock_silver)
```

## Features

### 1. Data Quality Validations ✓

- **Price Validation**: Ensures prices are positive and follow OHLC rules (High ≥ Low, High ≥ Close, etc.)
- **Volume Validation**: Checks that volume is non-negative
- **Completeness Check**: Validates required fields (symbol, sector, event_time)

### 2. Deduplication 🔄

- Removes duplicate records for the same (symbol, event_time) pair
- Keeps the latest record based on `ingest_time`

### 3. Anomaly Detection 🚨

- Detects price movements > 50% in a single tick
- Identifies volume spikes > 10x previous value
- Flags anomalies without removing data

### 4. Data Imputation 🔧

- Handles missing OHLC values using intelligent fallback:
  - Missing `open`, `high`, `low` → use `close` value
  - Tracks imputation with boolean flags

### 5. Quality Metrics 📊

- Real-time batch quality reporting
- Per-batch statistics on validations, anomalies, and imputations
- Per-symbol quality tracking

## Silver Table Schema

```sql
CREATE TABLE stock_silver (
    -- Original data fields
    symbol STRING,
    sector STRING,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume LONG,
    event_time TIMESTAMP,
    source STRING,
    ingest_time TIMESTAMP,
    processed_time TIMESTAMP,

    -- Data quality flags
    is_valid_price BOOLEAN,
    is_valid_volume BOOLEAN,
    is_complete_record BOOLEAN,
    has_anomaly BOOLEAN,

    -- Imputation indicators
    open_imputed BOOLEAN,
    high_imputed BOOLEAN,
    low_imputed BOOLEAN,
    close_imputed BOOLEAN
) USING iceberg
PARTITIONED BY (days(processed_time))
```

### Partitioning Strategy

- **Partition Key**: `days(processed_time)`
- **Benefits**: Efficient time-based queries and pruning

## Scripts

### 1. `bronze_to_silver.py`

Main Silver layer processing script that reads from Bronze, applies transformations, and writes to Silver.

**Features**:

- Streaming processing from Bronze table
- Micro-batch processing with quality metrics
- Checkpoint management for fault tolerance
- Configurable processing interval (default: 10 seconds)

**Environment Variables**:

```bash
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
ICEBERG_WAREHOUSE=s3a://warehouse
CHECKPOINT_LOCATION_SILVER=/checkpoints/iceberg_silver
```

### 2. `query_iceberg_silver.py`

Query and analyze Silver layer data with comprehensive statistics.

**Outputs**:

- Sample records from Silver table
- Overall data quality statistics
- Per-symbol statistics
- Detected anomalies
- Records with imputed values

## Usage

### Start Silver Layer Processing

```bash
# Set environment variables (if not using .env)
export MINIO_ENDPOINT=http://localhost:9000
export MINIO_ACCESS_KEY=minioadmin
export MINIO_SECRET_KEY=minioadmin
export ICEBERG_WAREHOUSE=s3a://warehouse
export CHECKPOINT_LOCATION_SILVER=/checkpoints/iceberg_silver

# Run Silver layer processor
cd processed_data_silver
python bronze_to_silver.py
```

### Query Silver Data

```bash
cd processed_data_silver
python query_iceberg_silver.py
```

## Data Quality Checks

### Price Validation Logic

```python
is_valid_price = (
    close > 0 AND
    open > 0 AND
    high >= low AND
    high >= close AND
    low <= close
)
```

### Anomaly Detection Logic

```python
has_anomaly = (
    abs(close - prev_close) / prev_close > 0.5  # 50% price change
    OR
    volume > prev_volume * 10  # 10x volume spike
)
```

### Deduplication Logic

```python
# Keep latest record per (symbol, event_time)
PARTITION BY (symbol, event_time)
ORDER BY ingest_time DESC
LIMIT 1
```

## Monitoring & Metrics

Each micro-batch displays:

```
📊 Batch Quality Metrics:
   Total records:      250
   Valid prices:       248 (99.2%)
   Valid volumes:      250 (100.0%)
   Complete records:   250 (100.0%)
   Anomalies detected: 3
   Imputed values:     2
```

## Best Practices

### 1. Checkpoint Management

- Checkpoints stored at: `/checkpoints/iceberg_silver`
- For production, use MinIO: `s3a://warehouse/checkpoints/iceberg_silver`

### 2. Processing Interval

- Default: 10 seconds
- Adjust based on data volume: `.trigger(processingTime="30 seconds")`

### 3. Quality Thresholds

Current thresholds are configurable:

- Price change anomaly: 50% → modify in `process_silver_batch()`
- Volume spike anomaly: 10x → modify in `process_silver_batch()`

### 4. Recovery from Failure

Spark Structured Streaming with checkpoints ensures:

- Exactly-once processing semantics
- Automatic recovery from failures
- No data loss on restart

## Integration with Bronze Layer

**Prerequisites**:

1. Bronze layer must be running and writing to `stock_bronze`
2. MinIO must be accessible
3. Iceberg catalog properly configured

**Data Flow Timeline**:

```
T+0s:  Data arrives in Bronze
T+10s: Silver processes first batch
T+20s: Silver processes second batch
...
```

## Next Steps: Gold Layer

The Silver layer produces clean data ready for:

- **Aggregations**: Daily OHLC, moving averages
- **Feature Engineering**: Technical indicators (RSI, MACD, Bollinger Bands)
- **Analytics**: Sector performance, correlation analysis
- **ML Models**: Price prediction, anomaly detection models

## Troubleshooting

### Issue: No data in Silver table

```bash
# Check if Bronze has data
python query_iceberg_bronze.py

# Check Silver query status
# Look for "No data to process" messages
```

### Issue: Checkpoints conflict

```bash
# Clear checkpoints and restart
rm -rf /checkpoints/iceberg_silver
python bronze_to_silver.py
```

### Issue: Memory errors

```python
# Increase Spark memory in bronze_to_silver.py
.config("spark.driver.memory", "4g")
.config("spark.executor.memory", "4g")
```

## Performance Tuning

### 1. Partition Tuning

```python
# Adjust shuffle partitions based on data volume
.config("spark.sql.shuffle.partitions", "8")  # default: 4
```

### 2. Batch Size

```python
# Larger intervals for high-volume data
.trigger(processingTime="30 seconds")
```

### 3. Iceberg Table Maintenance

```sql
-- Compact small files periodically
CALL local.system.rewrite_data_files('stock_db.stock_silver');

-- Expire old snapshots
CALL local.system.expire_snapshots('stock_db.stock_silver', TIMESTAMP '2025-01-01 00:00:00');
```

## Architecture Decisions

### Why Streaming vs Batch?

- **Streaming**: Near real-time data quality feedback
- **Batch**: Would introduce latency in detecting issues

### Why Micro-batches?

- Better control over quality metrics per batch
- Easier to log and monitor processing
- Flexible checkpoint management

### Why Partitioning by processed_time?

- Aligns with data lifecycle
- Efficient time-range queries
- Easy data retention policies

## References

- [Apache Iceberg Documentation](https://iceberg.apache.org/)
- [Spark Structured Streaming Guide](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Data Quality Best Practices](https://databricks.com/blog/2019/08/14/productionizing-machine-learning-with-delta-lake.html)
