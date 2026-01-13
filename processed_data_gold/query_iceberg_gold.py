"""
Query Gold Layer Data
- Read from stock_gold_realtime Iceberg table
- Display technical indicators and trading signals
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, desc

# Get configuration from environment variables
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
ICEBERG_WAREHOUSE = os.getenv("ICEBERG_WAREHOUSE", "s3a://warehouse")

# Initialize SparkSession
spark = (
    SparkSession.builder.appName("Query-Gold-Layer")
    .master("local[*]")
    .config(
        "spark.jars.packages",
        "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,"
        "org.apache.hadoop:hadoop-aws:3.3.4,"
        "com.amazonaws:aws-java-sdk-bundle:1.12.367",
    )
    .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.local.type", "hadoop")
    .config("spark.sql.catalog.local.warehouse", ICEBERG_WAREHOUSE)
    .config("spark.sql.defaultCatalog", "local")
    .config(
        "spark.sql.extensions",
        "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
    )
    .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
    .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
    .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("=" * 80)
print("QUERY GOLD LAYER DATA - Technical Indicators & Trading Signals")
print("=" * 80)

spark.sql("USE stock_db")


# Read Gold table
print("\n📊 Reading from stock_gold_realtime table...")
gold_df = spark.read.format("iceberg").table("stock_gold_realtime")

total_records = gold_df.count()
print(f"✓ Total records in Gold: {total_records}\n")

if total_records == 0:
    print("⚠️  No data in Gold layer yet. Make sure the streaming processor is running.")
    spark.stop()
    exit()

# Display schema
print("=" * 80)
print("GOLD TABLE SCHEMA")
print("=" * 80)
gold_df.printSchema()

# Get latest records per symbol
print("\n" + "=" * 80)
print("LATEST TRADING SIGNALS (Most Recent per Symbol)")
print("=" * 80)

latest_signals = spark.sql(
    """
    SELECT symbol, sector, close, price_change_pct, 
           sma_5, sma_20, rsi_14, macd, macd_signal,
           signal_score, recommendation, event_time
    FROM (
        SELECT *, 
               ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY event_time DESC) as rn
        FROM stock_gold_realtime
    ) 
    WHERE rn = 1
    ORDER BY signal_score DESC
"""
)

latest_signals.show(50, truncate=False)

# Trading Signals Summary
print("\n" + "=" * 80)
print("TRADING SIGNALS SUMMARY")
print("=" * 80)

signal_summary = spark.sql(
    """
    SELECT recommendation, COUNT(*) as count
    FROM (
        SELECT *, 
               ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY event_time DESC) as rn
        FROM stock_gold_realtime
    ) 
    WHERE rn = 1
    GROUP BY recommendation
    ORDER BY recommendation
"""
)

signal_summary.show(truncate=False)

# Technical Indicators - Buy Signals
print("\n" + "=" * 80)
print("🟢 STRONG BUY & BUY SIGNALS")
print("=" * 80)

buy_signals = spark.sql(
    """
    SELECT symbol, sector, close, rsi_14, macd, signal_score, recommendation
    FROM (
        SELECT *, 
               ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY event_time DESC) as rn
        FROM stock_gold_realtime
    ) 
    WHERE rn = 1 AND recommendation IN ('BUY', 'STRONG BUY')
    ORDER BY signal_score DESC
"""
)

if buy_signals.count() > 0:
    buy_signals.show(20, truncate=False)
else:
    print("No buy signals detected")

# Technical Indicators - Sell Signals
print("\n" + "=" * 80)
print("🔴 STRONG SELL & SELL SIGNALS")
print("=" * 80)

sell_signals = spark.sql(
    """
    SELECT symbol, sector, close, rsi_14, macd, signal_score, recommendation
    FROM (
        SELECT *, 
               ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY event_time DESC) as rn
        FROM stock_gold_realtime
    ) 
    WHERE rn = 1 AND recommendation IN ('SELL', 'STRONG SELL')
    ORDER BY signal_score ASC
"""
)

if sell_signals.count() > 0:
    sell_signals.show(20, truncate=False)
else:
    print("No sell signals detected")

# Golden Cross & Death Cross
print("\n" + "=" * 80)
print("📊 GOLDEN CROSS & DEATH CROSS EVENTS")
print("=" * 80)

crosses = spark.sql(
    """
    SELECT symbol, sector, close, sma_5, sma_20, 
           golden_cross, death_cross, event_time
    FROM (
        SELECT *, 
               ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY event_time DESC) as rn
        FROM stock_gold_realtime
    ) 
    WHERE rn = 1 AND (golden_cross = true OR death_cross = true)
    ORDER BY event_time DESC
"""
)

if crosses.count() > 0:
    crosses.show(20, truncate=False)
else:
    print("No recent golden/death cross events")

# RSI Extremes
print("\n" + "=" * 80)
print("⚠️  RSI EXTREMES (Oversold/Overbought)")
print("=" * 80)

rsi_extremes = spark.sql(
    """
    SELECT symbol, sector, close, rsi_14, 
           rsi_oversold, rsi_overbought, recommendation
    FROM (
        SELECT *, 
               ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY event_time DESC) as rn
        FROM stock_gold_realtime
    ) 
    WHERE rn = 1 AND (rsi_oversold = true OR rsi_overbought = true)
    ORDER BY rsi_14
"""
)

if rsi_extremes.count() > 0:
    rsi_extremes.show(20, truncate=False)
else:
    print("No RSI extremes detected")

# Sector Performance
print("\n" + "=" * 80)
print("🏢 SECTOR PERFORMANCE")
print("=" * 80)

sector_perf = spark.sql(
    """
    SELECT sector,
           COUNT(DISTINCT symbol) as stock_count,
           ROUND(AVG(close), 2) as avg_price,
           ROUND(AVG(price_change_pct), 2) as avg_change_pct,
           ROUND(AVG(rsi_14), 1) as avg_rsi,
           SUM(volume) as total_volume
    FROM (
        SELECT *, 
               ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY event_time DESC) as rn
        FROM stock_gold_realtime
    ) 
    WHERE rn = 1
    GROUP BY sector
    ORDER BY avg_change_pct DESC
"""
)

sector_perf.show(truncate=False)

# Top Performers
print("\n" + "=" * 80)
print("🏆 TOP 10 PERFORMERS (by % change)")
print("=" * 80)

top_performers = spark.sql(
    """
    SELECT symbol, sector, close, price_change_pct, volume, recommendation
    FROM (
        SELECT *, 
               ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY event_time DESC) as rn
        FROM stock_gold_realtime
    ) 
    WHERE rn = 1
    ORDER BY price_change_pct DESC
    LIMIT 10
"""
)

top_performers.show(truncate=False)

# Bottom Performers
print("\n" + "=" * 80)
print("📉 BOTTOM 10 PERFORMERS (by % change)")
print("=" * 80)

bottom_performers = spark.sql(
    """
    SELECT symbol, sector, close, price_change_pct, volume, recommendation
    FROM (
        SELECT *, 
               ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY event_time DESC) as rn
        FROM stock_gold_realtime
    ) 
    WHERE rn = 1
    ORDER BY price_change_pct ASC
    LIMIT 10
"""
)

bottom_performers.show(truncate=False)

print("\n" + "=" * 80)
print("QUERY COMPLETED")
print("=" * 80)

spark.stop()
