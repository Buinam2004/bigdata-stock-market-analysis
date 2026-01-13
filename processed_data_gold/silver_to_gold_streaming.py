"""
Gold Layer: Real-time Technical Indicators & Analytics
- Reads streaming data from Silver layer (stock_silver)
- Calculates technical indicators in real-time:
  * Moving Averages (SMA 5, 20, 50)
  * RSI (Relative Strength Index)
  * MACD (Moving Average Convergence Divergence)
  * Bollinger Bands
  * Volume metrics
- Generates trading signals
- Writes to Gold Iceberg table (stock_gold_realtime)
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    current_timestamp,
    lit,
    when,
    avg,
    stddev,
    sum as spark_sum,
    count,
    lag,
    row_number,
    round as spark_round,
    min as spark_min,
    max as spark_max,
)
from pyspark.sql.window import Window

# Get configuration from environment variables
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
ICEBERG_WAREHOUSE = os.getenv("ICEBERG_WAREHOUSE", "s3a://warehouse")
CHECKPOINT_LOCATION = os.getenv(
    "CHECKPOINT_LOCATION_GOLD", "./checkpoints/iceberg_gold"
)

# Initialize SparkSession with Iceberg support
spark = (
    SparkSession.builder.appName("Gold-Layer-Realtime-Analytics")
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
    .config("spark.driver.memory", "2g")
    .config("spark.executor.memory", "2g")
    .config("spark.sql.shuffle.partitions", "4")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("=" * 80)
print("GOLD LAYER: Real-time Technical Indicators & Analytics")
print("=" * 80)
print("SparkSession initialized!")
print(f"Warehouse: {ICEBERG_WAREHOUSE}")
print(f"Checkpoint: {CHECKPOINT_LOCATION}")

spark.sql("USE stock_db")

# Create Gold table for real-time metrics
print("\n" + "=" * 80)
print("Creating Gold Table: stock_gold_realtime")
print("=" * 80)

spark.sql(
    """
CREATE TABLE IF NOT EXISTS stock_gold_realtime (
    symbol STRING,
    sector STRING,
    event_time TIMESTAMP,
    
    -- Price data
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
    
    -- Price changes
    price_change DOUBLE,
    price_change_pct DOUBLE,
    
    -- RSI (Relative Strength Index)
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
    
    -- Volume metrics
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
    
    -- Signal strength
    signal_score INT,
    recommendation STRING,
    
    -- Metadata
    processed_time TIMESTAMP
) USING iceberg
PARTITIONED BY (hours(processed_time))
"""
)

print("✓ Table stock_gold_realtime created successfully!")

# Read streaming data from Silver table
print("\n" + "=" * 80)
print("Reading streaming data from Silver table...")
print("=" * 80)

silver_stream = (
    spark.readStream.format("iceberg")
    .option("stream-from-timestamp", "0")
    .table("stock_silver")
)

print("✓ Connected to stock_silver table")


def calculate_ema(values, period):
    """Calculate Exponential Moving Average"""
    multiplier = 2.0 / (period + 1)
    # Simplified EMA calculation using window functions
    return values  # Placeholder - actual EMA requires iterative calculation


def process_gold_batch(batch_df, batch_id):
    """
    Process each micro-batch with technical indicator calculations
    """
    if batch_df.isEmpty():
        print(f"[BATCH {batch_id}] No data to process")
        return

    print(f"\n{'=' * 80}")
    print(f"[BATCH {batch_id}] Processing {batch_df.count()} records")
    print(f"{'=' * 80}")

    # Filter only valid records from Silver
    df = batch_df.filter(
        (col("is_valid_price") == True) & (col("is_complete_record") == True)
    ).select("symbol", "sector", "event_time", "open", "high", "low", "close", "volume")

    if df.isEmpty():
        print(f"  ⚠ No valid records to process")
        return

    # Define window specifications
    symbol_window = Window.partitionBy("symbol").orderBy("event_time")

    # Window for last N rows
    window_5 = symbol_window.rowsBetween(-4, 0)
    window_20 = symbol_window.rowsBetween(-19, 0)
    window_50 = symbol_window.rowsBetween(-49, 0)

    # Step 1: Calculate Simple Moving Averages
    print(f"  📊 Calculating Moving Averages...")
    df_ma = (
        df.withColumn("sma_5", avg("close").over(window_5))
        .withColumn("sma_20", avg("close").over(window_20))
        .withColumn("sma_50", avg("close").over(window_50))
        .withColumn(
            "ema_12",
            avg("close").over(
                Window.partitionBy("symbol").orderBy("event_time").rowsBetween(-11, 0)
            ),
        )
    )

    # Step 2: Calculate price changes
    df_changes = (
        df_ma.withColumn("prev_close", lag("close", 1).over(symbol_window))
        .withColumn("price_change", col("close") - col("prev_close"))
        .withColumn(
            "price_change_pct",
            when(
                col("prev_close") > 0,
                (col("close") - col("prev_close")) / col("prev_close") * 100,
            ).otherwise(0),
        )
    )

    # Step 3: Calculate RSI (Relative Strength Index)
    print(f"  📈 Calculating RSI...")
    df_rsi = (
        df_changes.withColumn(
            "gain", when(col("price_change") > 0, col("price_change")).otherwise(0)
        )
        .withColumn(
            "loss", when(col("price_change") < 0, -col("price_change")).otherwise(0)
        )
        .withColumn(
            "avg_gain",
            avg("gain").over(
                Window.partitionBy("symbol").orderBy("event_time").rowsBetween(-13, 0)
            ),
        )
        .withColumn(
            "avg_loss",
            avg("loss").over(
                Window.partitionBy("symbol").orderBy("event_time").rowsBetween(-13, 0)
            ),
        )
        .withColumn(
            "rs",
            when(col("avg_loss") > 0, col("avg_gain") / col("avg_loss")).otherwise(100),
        )
        .withColumn("rsi_14", 100 - (100 / (1 + col("rs"))))
        .drop("gain", "loss", "avg_gain", "avg_loss", "rs")
    )

    # Step 4: Calculate MACD
    print(f"  📉 Calculating MACD...")
    window_12 = Window.partitionBy("symbol").orderBy("event_time").rowsBetween(-11, 0)
    window_26 = Window.partitionBy("symbol").orderBy("event_time").rowsBetween(-25, 0)
    window_9 = Window.partitionBy("symbol").orderBy("event_time").rowsBetween(-8, 0)

    df_macd = (
        df_rsi.withColumn("ema_12_temp", avg("close").over(window_12))
        .withColumn("ema_26", avg("close").over(window_26))
        .withColumn("macd", col("ema_12_temp") - col("ema_26"))
        .withColumn("macd_signal", avg("macd").over(window_9))
        .withColumn("macd_histogram", col("macd") - col("macd_signal"))
        .drop("ema_12_temp", "ema_26")
    )

    # Step 5: Calculate Bollinger Bands
    print(f"  📊 Calculating Bollinger Bands...")
    df_bb = (
        df_macd.withColumn("bb_middle", col("sma_20"))
        .withColumn("std_20", stddev("close").over(window_20))
        .withColumn("bb_upper", col("bb_middle") + (2 * col("std_20")))
        .withColumn("bb_lower", col("bb_middle") - (2 * col("std_20")))
        .withColumn("bb_width", col("bb_upper") - col("bb_lower"))
        .drop("std_20")
    )

    # Step 6: Calculate Volume metrics
    print(f"  📦 Calculating Volume Metrics...")
    df_volume = df_bb.withColumn(
        "volume_sma_20", avg("volume").over(window_20)
    ).withColumn(
        "volume_ratio",
        when(col("volume_sma_20") > 0, col("volume") / col("volume_sma_20")).otherwise(
            1
        ),
    )

    # Step 7: Calculate Volatility (20-period standard deviation)
    df_volatility = df_volume.withColumn(
        "volatility_20", stddev("close").over(window_20)
    )

    # Step 8: Generate Trading Signals
    print(f"  🎯 Generating Trading Signals...")

    df_signals = (
        df_volatility.withColumn("prev_sma_5", lag("sma_5", 1).over(symbol_window))
        .withColumn("prev_sma_20", lag("sma_20", 1).over(symbol_window))
        .withColumn(
            "golden_cross",
            (col("sma_5") > col("sma_20")) & (col("prev_sma_5") <= col("prev_sma_20")),
        )
        .withColumn(
            "death_cross",
            (col("sma_5") < col("sma_20")) & (col("prev_sma_5") >= col("prev_sma_20")),
        )
        .withColumn("rsi_oversold", col("rsi_14") < 30)
        .withColumn("rsi_overbought", col("rsi_14") > 70)
        .withColumn(
            "macd_bullish",
            (col("macd") > col("macd_signal")) & (col("macd_histogram") > 0),
        )
        .withColumn(
            "macd_bearish",
            (col("macd") < col("macd_signal")) & (col("macd_histogram") < 0),
        )
        .withColumn("bb_squeeze", col("bb_width") < col("bb_middle") * 0.1)
        .drop("prev_sma_5", "prev_sma_20", "prev_close")
    )

    # Step 9: Calculate Signal Score and Recommendation
    df_final = (
        df_signals.withColumn(
            "signal_score",
            when(col("golden_cross"), 2).otherwise(0)
            + when(col("death_cross"), -2).otherwise(0)
            + when(col("rsi_oversold"), 1).otherwise(0)
            + when(col("rsi_overbought"), -1).otherwise(0)
            + when(col("macd_bullish"), 1).otherwise(0)
            + when(col("macd_bearish"), -1).otherwise(0),
        )
        .withColumn(
            "recommendation",
            when(col("signal_score") >= 2, "STRONG BUY")
            .when(col("signal_score") == 1, "BUY")
            .when(col("signal_score") == -1, "SELL")
            .when(col("signal_score") <= -2, "STRONG SELL")
            .otherwise("HOLD"),
        )
        .withColumn("processed_time", current_timestamp())
    )

    # Step 10: Quality metrics for this batch
    total_records = df_final.count()
    buy_signals = df_final.filter(
        col("recommendation").isin(["BUY", "STRONG BUY"])
    ).count()
    sell_signals = df_final.filter(
        col("recommendation").isin(["SELL", "STRONG SELL"])
    ).count()
    hold_signals = df_final.filter(col("recommendation") == "HOLD").count()

    print(f"\n  📊 Batch Analytics:")
    print(f"     Total records:     {total_records}")
    print(
        f"     BUY signals:       {buy_signals} ({buy_signals/total_records*100:.1f}%)"
    )
    print(
        f"     SELL signals:      {sell_signals} ({sell_signals/total_records*100:.1f}%)"
    )
    print(
        f"     HOLD signals:      {hold_signals} ({hold_signals/total_records*100:.1f}%)"
    )

    # Show sample recommendations
    print(f"\n  🎯 Sample Recommendations:")
    df_final.select(
        "symbol", "close", "sma_5", "sma_20", "rsi_14", "signal_score", "recommendation"
    ).filter(col("recommendation") != "HOLD").show(5, truncate=False)

    # Step 11: Write to Gold table
    print(f"\n  💾 Writing to stock_gold_realtime table...")
    df_final.writeTo("local.stock_db.stock_gold_realtime").append()

    print(f"  ✓ Batch {batch_id} completed successfully!")
    print(f"{'=' * 80}\n")


# Start streaming query with foreachBatch
print("\n" + "=" * 80)
print("Starting Gold Layer Streaming Query...")
print("=" * 80)

gold_query = (
    silver_stream.writeStream.foreachBatch(process_gold_batch)
    .option("checkpointLocation", CHECKPOINT_LOCATION)
    .trigger(processingTime="15 seconds")  # Process every 15 seconds
    .start()
)

print("\n✓ Gold Layer streaming query STARTED!")
print(f"  Query ID: {gold_query.id}")
print(f"  Processing interval: 15 seconds")
print(f"  Output: stock_db.stock_gold_realtime")
print("\n" + "=" * 80)
print("📊 Real-time Technical Indicators Active!")
print("🎯 Trading Signals Being Generated!")
print("\nPress Ctrl+C to stop.")
print("=" * 80 + "\n")

# Wait for termination
try:
    gold_query.awaitTermination()
except KeyboardInterrupt:
    print("\n\nStopping Gold Layer query...")
    gold_query.stop()
    print("✓ Query stopped successfully!")
