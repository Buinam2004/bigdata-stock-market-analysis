"""
Query Silver Layer Data
- Read from stock_silver Iceberg table
- Display cleansed data with quality metrics
- Show data quality statistics
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum as _sum, avg, when

# Get configuration from environment variables
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
ICEBERG_WAREHOUSE = os.getenv("ICEBERG_WAREHOUSE", "s3a://warehouse")

# Initialize SparkSession
spark = (
    SparkSession.builder.appName("Query-Silver-Layer")
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
print("QUERY SILVER LAYER DATA")
print("=" * 80)

# Use database
spark.sql("USE stock_db")

# Read Silver table
print("\n📊 Reading from stock_silver table...")
silver_df = spark.read.format("iceberg").table("stock_silver")

print(f"✓ Total records in Silver: {silver_df.count()}\n")

spark.sql("DESCRIBE EXTENDED local.stock_db.stock_silver").show(truncate=False)


spark.sql("SELECT * FROM local.stock_db.stock_silver.snapshots").show(truncate=False)


spark.table("local.stock_db.stock_silver").inputFiles()[:20]  # show up to 20 paths


# Display schema
print("=" * 80)
print("SILVER TABLE SCHEMA")
print("=" * 80)
silver_df.printSchema()

# Show sample data
print("\n" + "=" * 80)
print("SAMPLE RECORDS (Latest 20)")
print("=" * 80)
silver_df.orderBy(col("processed_time").desc()).select(
    "symbol",
    "sector",
    "close",
    "volume",
    "event_time",
    "is_valid_price",
    "is_valid_volume",
    "has_anomaly",
).show(20, truncate=False)

# Data Quality Statistics
print("\n" + "=" * 80)
print("DATA QUALITY STATISTICS")
print("=" * 80)

total_records = silver_df.count()

if total_records > 0:
    quality_stats = silver_df.agg(
        count("*").alias("total_records"),
        _sum(when(col("is_valid_price"), 1).otherwise(0)).alias("valid_price_count"),
        _sum(when(col("is_valid_volume"), 1).otherwise(0)).alias("valid_volume_count"),
        _sum(when(col("is_complete_record"), 1).otherwise(0)).alias(
            "complete_record_count"
        ),
        _sum(when(col("has_anomaly"), 1).otherwise(0)).alias("anomaly_count"),
        _sum(
            when(
                col("open_imputed")
                | col("high_imputed")
                | col("low_imputed")
                | col("close_imputed"),
                1,
            ).otherwise(0)
        ).alias("imputed_count"),
    ).collect()[0]

    print(f"\nTotal Records:          {quality_stats['total_records']}")
    print(
        f"Valid Prices:           {quality_stats['valid_price_count']} "
        f"({quality_stats['valid_price_count']/total_records*100:.1f}%)"
    )
    print(
        f"Valid Volumes:          {quality_stats['valid_volume_count']} "
        f"({quality_stats['valid_volume_count']/total_records*100:.1f}%)"
    )
    print(
        f"Complete Records:       {quality_stats['complete_record_count']} "
        f"({quality_stats['complete_record_count']/total_records*100:.1f}%)"
    )
    print(
        f"Anomalies Detected:     {quality_stats['anomaly_count']} "
        f"({quality_stats['anomaly_count']/total_records*100:.1f}%)"
    )
    print(
        f"Records with Imputation: {quality_stats['imputed_count']} "
        f"({quality_stats['imputed_count']/total_records*100:.1f}%)"
    )

    # Per-Symbol Statistics
    print("\n" + "=" * 80)
    print("PER-SYMBOL STATISTICS")
    print("=" * 80)

    symbol_stats = (
        silver_df.groupBy("symbol", "sector")
        .agg(
            count("*").alias("record_count"),
            avg("close").alias("avg_close"),
            avg("volume").alias("avg_volume"),
            _sum(when(col("has_anomaly"), 1).otherwise(0)).alias("anomaly_count"),
        )
        .orderBy(col("record_count").desc())
    )

    symbol_stats.show(50, truncate=False)

    # Show anomalies if any
    anomalies_df = silver_df.filter(col("has_anomaly") == True)
    anomaly_count = anomalies_df.count()

    if anomaly_count > 0:
        print("\n" + "=" * 80)
        print(f"DETECTED ANOMALIES ({anomaly_count} records)")
        print("=" * 80)
        anomalies_df.select(
            "symbol", "close", "volume", "event_time", "has_anomaly"
        ).orderBy(col("event_time").desc()).show(20, truncate=False)
    else:
        print("\n✓ No anomalies detected in the data")

    # Show imputed records
    imputed_df = silver_df.filter(
        col("open_imputed")
        | col("high_imputed")
        | col("low_imputed")
        | col("close_imputed")
    )
    imputed_count = imputed_df.count()

    if imputed_count > 0:
        print("\n" + "=" * 80)
        print(f"RECORDS WITH IMPUTATION ({imputed_count} records)")
        print("=" * 80)
        imputed_df.select(
            "symbol",
            "open",
            "high",
            "low",
            "close",
            "open_imputed",
            "high_imputed",
            "low_imputed",
            "close_imputed",
        ).show(20, truncate=False)
    else:
        print("\n✓ No imputed values in the data")
else:
    print("\n⚠ No records found in Silver table")

print("\n" + "=" * 80)
print("QUERY COMPLETED")
print("=" * 80)

spark.stop()
