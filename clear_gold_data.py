"""
Clear Gold Table and Checkpoints
Run this after fixing the code to start fresh
"""

from pyspark.sql import SparkSession
import shutil
import os

spark = (
    SparkSession.builder.appName("Clear-Gold-Data")
    .master("local[*]")
    .config(
        "spark.jars.packages",
        "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,"
        "org.apache.hadoop:hadoop-aws:3.3.4,"
        "com.amazonaws:aws-java-sdk-bundle:1.12.367",
    )
    .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.local.type", "hadoop")
    .config("spark.sql.catalog.local.warehouse", "s3a://warehouse")
    .config("spark.sql.defaultCatalog", "local")
    .config(
        "spark.sql.extensions",
        "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
    )
    .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:9000")
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")
spark.sql("USE stock_db")

print("=" * 80)
print("CLEARING GOLD LAYER DATA")
print("=" * 80)

# Check current data
count = spark.sql("SELECT COUNT(*) as cnt FROM stock_gold_realtime").collect()[0]["cnt"]
print(f"\nCurrent records in gold table: {count}")

if count > 0:
    response = input("\nDo you want to delete all gold data? (yes/no): ")
    if response.lower() == "yes":
        print("\nDeleting all records from stock_gold_realtime...")
        spark.sql("DELETE FROM stock_gold_realtime WHERE true")
        print("✓ All records deleted")

        # Clear checkpoints
        checkpoint_path = "./processed_data_gold/checkpoints/iceberg_gold"
        if os.path.exists(checkpoint_path):
            print(f"\nClearing checkpoint directory: {checkpoint_path}")
            shutil.rmtree(checkpoint_path)
            print("✓ Checkpoint cleared")

        print("\n" + "=" * 80)
        print("Gold layer cleared successfully!")
        print("You can now restart the gold streaming pipeline.")
        print("=" * 80)
    else:
        print("Cancelled.")
else:
    print("Gold table is already empty.")

spark.stop()
