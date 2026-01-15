"""
Silver Layer: Data Cleansing and Quality Enhancement
- Reads from Bronze Iceberg table (stock_bronze)
- Applies data quality validations
- Deduplicates records
- Handles null/invalid values
- Adds quality flags and metadata
- Writes to Silver Iceberg table (stock_silver)
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    current_timestamp,
    lit,
    when,
    row_number,
    coalesce,
    lead,
    lag,
    mean,
    abs as spark_abs,
)
from pyspark.sql.window import Window

# Get configuration from environment variables
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
ICEBERG_WAREHOUSE = os.getenv("ICEBERG_WAREHOUSE", "s3a://warehouse")
CHECKPOINT_LOCATION = os.getenv(
    "CHECKPOINT_LOCATION_SILVER", "/checkpoints/iceberg_silver"
)

# Initialize SparkSession with Iceberg support + MinIO S3
spark = (
    SparkSession.builder.appName("Silver-Layer-Data-Quality")
    .master("local[*]")
    .config(
        "spark.jars.packages",
        "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,"
        "org.apache.hadoop:hadoop-aws:3.3.4,"
        "com.amazonaws:aws-java-sdk-bundle:1.12.367",
    )
    # Iceberg Catalog Configuration
    .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.local.type", "hadoop")
    .config("spark.sql.catalog.local.warehouse", ICEBERG_WAREHOUSE)
    .config("spark.sql.defaultCatalog", "local")
    .config(
        "spark.sql.extensions",
        "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
    )
    # S3/MinIO Configuration
    .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
    .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
    .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    # Memory settings
    .config("spark.driver.memory", "2g")
    .config("spark.executor.memory", "2g")
    .config("spark.sql.shuffle.partitions", "4")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("SILVER LAYER: Data Quality & Cleansing")
print(f"Warehouse: {ICEBERG_WAREHOUSE}")
print(f"Checkpoint: {CHECKPOINT_LOCATION}")

# Use stock_db database
spark.sql("USE stock_db")

spark.sql(
    """
CREATE TABLE IF NOT EXISTS stock_silver (
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
    -- Cleansed/imputed indicators
    open_imputed BOOLEAN,
    high_imputed BOOLEAN,
    low_imputed BOOLEAN,
    close_imputed BOOLEAN
) USING iceberg
PARTITIONED BY (days(processed_time))
"""
)

bronze_stream = (
    spark.readStream.format("iceberg")
    .option("stream-from-timestamp", "0")  # Read all data from beginning
    .table("stock_bronze")
)


def process_silver_batch(batch_df, batch_id):
    """
    Process each micro-batch with data quality checks and cleansing
    """
    if batch_df.isEmpty():
        return

    # Step 1: Convert event_time to timestamp
    df = batch_df.withColumn("event_time", col("event_time").cast("timestamp"))

    # Step 2: Deduplicate - keep latest record for each (symbol, event_time)
    window_spec = Window.partitionBy("symbol", "event_time").orderBy(
        col("ingest_time").desc()
    )
    df_dedup = (
        df.withColumn("row_num", row_number().over(window_spec))
        .filter(col("row_num") == 1)
        .drop("row_num")
    )

    dedup_count = batch_df.count() - df_dedup.count()
    if dedup_count > 0:
        print(f"  ⚠ Removed {dedup_count} duplicate records")

    # Step 3: Data quality validations
    df_validated = (
        df_dedup.withColumn(
            "is_valid_price",
            (col("close").isNotNull())
            & (col("close") > 0)
            & (col("open") > 0)
            & (col("high") >= col("low"))
            & (col("high") >= col("close"))
            & (col("low") <= col("close")),
        )
        .withColumn(
            "is_valid_volume", (col("volume").isNotNull()) & (col("volume") >= 0)
        )
        .withColumn(
            "is_complete_record",
            col("symbol").isNotNull()
            & col("sector").isNotNull()
            & col("event_time").isNotNull(),
        )
    )

    # Step 4: Detect anomalies (simple outlier detection)
    # Anomaly: volume > 10x typical or price changes > 50% in one tick
    symbol_window = Window.partitionBy("symbol").orderBy("event_time")

    df_with_prev = df_validated.withColumn(
        "prev_close", lag("close", 1).over(symbol_window)
    ).withColumn("prev_volume", lag("volume", 1).over(symbol_window))

    df_anomaly = df_with_prev.withColumn(
        "has_anomaly",
        when(
            (col("prev_close").isNotNull())
            & (
                (spark_abs(col("close") - col("prev_close")) / col("prev_close") > 0.5)
                | (col("volume") > col("prev_volume") * 10)
            ),
            True,
        ).otherwise(False),
    ).drop("prev_close", "prev_volume")

    # Step 5: Handle missing/null values with forward fill
    # For price data, use previous close or set imputation flag
    df_imputed = (
        df_anomaly.withColumn("open_imputed", col("open").isNull())
        .withColumn(
            "open", when(col("open").isNull(), col("close")).otherwise(col("open"))
        )
        .withColumn("high_imputed", col("high").isNull())
        .withColumn(
            "high", when(col("high").isNull(), col("close")).otherwise(col("high"))
        )
        .withColumn("low_imputed", col("low").isNull())
        .withColumn(
            "low", when(col("low").isNull(), col("close")).otherwise(col("low"))
        )
        .withColumn("close_imputed", col("close").isNull())
        .withColumn(
            "close", when(col("close").isNull(), lit(0.0)).otherwise(col("close"))
        )
    )

    # Step 6: Add processing timestamp
    silver_df = df_imputed.withColumn("processed_time", current_timestamp())

    # Write to Silver table
    silver_df.writeTo("local.stock_db.stock_silver").append()


# Start streaming query with foreachBatch
print("Starting Silver Layer Streaming Query...")

silver_query = (
    bronze_stream.writeStream.foreachBatch(process_silver_batch)
    .option("checkpointLocation", CHECKPOINT_LOCATION)
    .trigger(processingTime="1 second")  # Minimum supported micro-batch interval
    .start()
)

print(f"Silver Layer streaming query STARTED (Query ID: {silver_query.id})")
print("Press Ctrl+C to stop.")

# Wait for termination
try:
    silver_query.awaitTermination()
except KeyboardInterrupt:
    print("\n\nStopping Silver Layer query...")
    silver_query.stop()
    print("✓ Query stopped successfully!")
