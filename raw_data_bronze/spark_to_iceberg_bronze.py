"""
Phase 4: Spark Structured Streaming -> Iceberg Bronze
- Doc streaming tu Kafka
- Them cot ingest_time va source
- Ghi vao bang stock_bronze (Iceberg)
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType
from pyspark.sql.functions import col, from_json, current_timestamp, lit

# Khoi tao SparkSession voi Iceberg support
spark = (
    SparkSession.builder
    .appName("Phase4-Spark-To-Iceberg-Bronze")
    .master("local[*]")
    .config("spark.jars.packages", 
            "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,"
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.7")
    # Iceberg Catalog Configuration
    .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.local.type", "hadoop")
    .config("spark.sql.catalog.local.warehouse", "D:/Bigdata/iceberg-warehouse")
    .config("spark.sql.defaultCatalog", "local")
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
    .config("spark.driver.extraJavaOptions", "-Dhadoop.home.dir=C:/spark-3.5.7-bin-hadoop3/hadoop")
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
spark.sql("""
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
""")
print("Table stock_bronze created successfully!")

# Doc streaming tu Kafka
print("\nReading streaming data from Kafka...")
kafka_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("subscribe", "stock_ticks")
    .option("startingOffsets", "latest")
    .load()
)

# Schema cho stock data
stock_schema = StructType([
    StructField("symbol", StringType()),
    StructField("sector", StringType()),
    StructField("open", DoubleType()),
    StructField("high", DoubleType()),
    StructField("low", DoubleType()),
    StructField("close", DoubleType()),
    StructField("volume", LongType()),
    StructField("event_time", StringType()),
    StructField("source", StringType())
])

# Parse JSON tu Kafka value
parsed_df = (
    kafka_df
    .select(from_json(col("value").cast("string"), stock_schema).alias("data"))
    .select("data.*")
)

# Buoc 4.2.1: Chuan hoa Bronze - Them ingest_time va source
bronze_df = (
    parsed_df
    .withColumn("ingest_time", current_timestamp())
    .withColumn("source", lit("yahoo_finance"))
)

print("\nBronze DataFrame schema:")
bronze_df.printSchema()

# Buoc 4.2.2: Write Streaming -> Iceberg
print("Starting streaming write to Iceberg Bronze...")
bronze_query = (
    bronze_df.writeStream
    .format("iceberg")
    .outputMode("append")
    .option("checkpointLocation", "D:/Bigdata/checkpoints/iceberg_bronze")
    .toTable("stock_bronze")
)

print("=" * 60)
print("Streaming to Iceberg Bronze STARTED!")
print(f"Query ID: {bronze_query.id}")
print("=" * 60)
print("\nData is being written to: D:/Bigdata/iceberg-warehouse/stock_db/stock_bronze")
print("\nTo verify, open another terminal and run:")
print("  spark-submit --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0 query_iceberg_bronze.py")
print("\nPress Ctrl+C to stop.")
print("=" * 60)

# Doi query chay
bronze_query.awaitTermination()
