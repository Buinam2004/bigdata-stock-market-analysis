"""
Phase 3: Kafka -> Spark Structured Streaming
- Spark doc du lieu streaming tu Kafka topic `stock_ticks`
- Parse JSON message thanh DataFrame
- Hien thi du lieu realtime
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType
from pyspark.sql.functions import col, from_json

# Khoi tao SparkSession
spark = (
    SparkSession.builder
    .appName("Phase3-Kafka-To-Spark")
    .master("local[*]")
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.7")
    .config("spark.driver.extraJavaOptions", "-Dhadoop.home.dir=C:/spark-3.5.7-bin-hadoop3/hadoop")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("=" * 60)
print("PHASE 3: Kafka -> Spark Structured Streaming")
print("=" * 60)
print("SparkSession initialized!")

# Doc streaming tu Kafka
print("\nReading streaming data from Kafka topic: stock_ticks")
kafka_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("subscribe", "stock_ticks")
    .option("startingOffsets", "earliest")
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

print("\nParsed DataFrame Schema:")
parsed_df.printSchema()

# Ghi ra console de xem du lieu streaming
print("\nStarting streaming query to console...")
print("Press Ctrl+C to stop.\n")

query = (
    parsed_df.writeStream
    .format("console")
    .outputMode("append")
    .option("truncate", False)
    .start()
)

# Doi query chay
query.awaitTermination()
