"""
Phase 5: Verify & Ban giao
Query Iceberg Bronze Table de verify pipeline hoat dong
"""

import os
from pyspark.sql import SparkSession

# Get configuration from environment variables
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
ICEBERG_WAREHOUSE = os.getenv("ICEBERG_WAREHOUSE", "s3a://warehouse")

# Khoi tao SparkSession voi Iceberg support + MinIO S3
spark = (
    SparkSession.builder.appName("Phase5-Verify-Iceberg-Bronze")
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
    # S3/MinIO Configuration
    .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
    .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
    .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("PHASE 5: VERIFY Bronze Layer")

# Check if table exists
spark.sql("SHOW TABLES IN stock_db").show()

# Check schema
spark.sql("DESCRIBE stock_db.stock_bronze").show(truncate=False)

# Count records
count_df = spark.sql("SELECT COUNT(*) as total_records FROM stock_db.stock_bronze")
count_df.show()
total = count_df.collect()[0]["total_records"]
print(f"Total records: {total}")

# Query sample data
spark.sql(
    """
SELECT symbol, close, volume, event_time
FROM stock_db.stock_bronze
ORDER BY ingest_time DESC
LIMIT 10
"""
).show(truncate=False)

# Check data over time
spark.sql(
    """
SELECT 
  DATE_FORMAT(ingest_time, 'yyyy-MM-dd HH:mm') as minute,
  COUNT(*) as records
FROM stock_db.stock_bronze
GROUP BY DATE_FORMAT(ingest_time, 'yyyy-MM-dd HH:mm')
ORDER BY minute DESC
LIMIT 10
"""
).show(truncate=False)

# Statistics by sector
spark.sql(
    """
SELECT 
  sector, 
  COUNT(*) as count, 
  ROUND(AVG(close), 2) as avg_close,
  ROUND(MIN(close), 2) as min_close,
  ROUND(MAX(close), 2) as max_close
FROM stock_db.stock_bronze
GROUP BY sector
ORDER BY count DESC
"""
).show()

# Top 10 symbols
spark.sql(
    """
SELECT 
  symbol, 
  sector,
  COUNT(*) as count,
  ROUND(AVG(close), 2) as avg_price
FROM stock_db.stock_bronze
GROUP BY symbol, sector
ORDER BY count DESC
LIMIT 10
"""
).show()

# Summary
print(f"\nVerification Summary: {total} records in Bronze layer")

spark.stop()
