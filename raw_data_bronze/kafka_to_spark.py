"""
Phase 3: Kafka -> Spark Structured Streaming
- Spark doc du lieu streaming tu Kafka topic `stock_ticks`
- Parse JSON message thanh DataFrame
- Hien thi du lieu realtime
"""

import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType
from pyspark.sql.functions import col, from_json

# Get Kafka bootstrap servers from environment
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# Set Python executable environment variables to avoid conflicts
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

# Ensure JAVA_HOME is set properly (fix path if needed)
if "JAVA_HOME" in os.environ:
    java_home = os.environ["JAVA_HOME"].rstrip("\\").rstrip("/")
    os.environ["JAVA_HOME"] = java_home

# Set Hadoop home to avoid warnings (Windows specific)
if not os.environ.get("HADOOP_HOME"):
    os.environ["HADOOP_HOME"] = os.path.dirname(sys.executable)

# Initialize Spark Session
spark = (
    SparkSession.builder.appName("Phase3-Kafka-To-Spark")
    .master("local[*]")
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.7")
    .config("spark.driver.memory", "2g")
    .config("spark.executor.memory", "1g")
    .config("spark.sql.shuffle.partitions", "2")
    .config("spark.driver.bindAddress", "127.0.0.1")
    .config("spark.driver.host", "localhost")
    .config("spark.ui.enabled", "false")
    .config("spark.sql.adaptive.enabled", "false")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("PHASE 3: Kafka -> Spark Structured Streaming")

# Read streaming from Kafka
kafka_df = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
    .option("subscribe", "stock_ticks")
    .option("startingOffsets", "earliest")
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

# Parse JSON from Kafka value
parsed_df = kafka_df.select(
    from_json(col("value").cast("string"), stock_schema).alias("data")
).select("data.*")

# Write to console
print("Starting streaming query to console...")
print("Press Ctrl+C to stop.\n")

query = (
    parsed_df.writeStream.format("console")
    .outputMode("append")
    .option("truncate", False)
    .start()
)

# Doi query chay
query.awaitTermination()
