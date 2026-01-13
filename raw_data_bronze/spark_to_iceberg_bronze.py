"""
Phase 4: Spark Structured Streaming -> Iceberg Bronze
- Doc streaming tu Kafka
- Them cot ingest_time va source
- Ghi vao bang stock_bronze (Iceberg)
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType
from pyspark.sql.functions import col, from_json, current_timestamp, lit

# Get configuration from environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
ICEBERG_WAREHOUSE = os.getenv("ICEBERG_WAREHOUSE", "s3a://warehouse")
CHECKPOINT_LOCATION = os.getenv("CHECKPOINT_LOCATION", "/checkpoints/iceberg_bronze")

# Khoi tao SparkSession voi Iceberg support + MinIO S3
spark = (
    SparkSession.builder.appName("Phase4-Spark-To-Iceberg-Bronze")
    .master("local[*]")
    .config(
        "spark.jars.packages",
        "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,"
        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.7,"
        "org.apache.hadoop:hadoop-aws:3.3.4,"
        "com.amazonaws:aws-java-sdk-bundle:1.12.367",
    )
    # Iceberg Catalog Configuration with S3
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

print("=" * 60)
print("PHASE 4: Spark Streaming -> Iceberg Bronze")
print("=" * 60)
print("SparkSession with Iceberg initialized!")
print(f"Catalog: {spark.conf.get('spark.sql.defaultCatalog')}")
print(f"Warehouse: {spark.conf.get('spark.sql.catalog.local.warehouse')}")

# Tao database neu chua co
print("\nCreating database: stock_db")
spark.sql("CREATE DATABASE IF NOT EXISTS stock_db")
spark.sql("USE stock_db")

# Tao bang Iceberg stock_bronze
print("Creating Iceberg table: stock_bronze")
spark.sql(
    """
CREATE TABLE IF NOT EXISTS stock_bronze (
    symbol STRING,
    sector STRING,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume LONG,
    event_time STRING,
    source STRING,
    ingest_time TIMESTAMP
) USING iceberg
"""
)
print("Table stock_bronze created successfully!")

# Doc streaming tu Kafka
print("\nReading streaming data from Kafka...")
kafka_df = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
    .option("subscribe", "stock_ticks")
    .option("startingOffsets", "latest")
    .load()
)

# Schema cho stock data
stock_schema = StructType(
    [
        StructField("symbol", StringType()),
        StructField("sector", StringType()),
        StructField("open", DoubleType()),
        StructField("high", DoubleType()),
        StructField("low", DoubleType()),
        StructField("close", DoubleType()),
        StructField("volume", LongType()),
        StructField("event_time", StringType()),
        StructField("source", StringType()),
    ]
)

# Parse JSON tu Kafka value
parsed_df = kafka_df.select(
    from_json(col("value").cast("string"), stock_schema).alias("data")
).select("data.*")

# Buoc 4.2.1: Chuan hoa Bronze - Them ingest_time va source
bronze_df = parsed_df.withColumn("ingest_time", current_timestamp()).withColumn(
    "source", lit("yahoo_finance")
)

print("\nBronze DataFrame schema:")
bronze_df.printSchema()

# Buoc 4.2.2: Write Streaming -> Iceberg
print("Starting streaming write to Iceberg Bronze...")
bronze_query = (
    bronze_df.writeStream.format("iceberg")
    .outputMode("append")
    .option("checkpointLocation", CHECKPOINT_LOCATION)
    .toTable("stock_bronze")
)

print("=" * 60)
print("Streaming to Iceberg Bronze STARTED!")
print(f"Query ID: {bronze_query.id}")
print("=" * 60)
print(f"\nData is being written to: {ICEBERG_WAREHOUSE}/stock_db/stock_bronze")
print(f"Checkpoint location: {CHECKPOINT_LOCATION}")
print("\nPress Ctrl+C to stop.")
print("=" * 60)

# Doi query chay
bronze_query.awaitTermination()
