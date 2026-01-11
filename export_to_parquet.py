"""
Export Iceberg Bronze data to Parquet format for easy sharing
Đơn giản nhất: Export ra Parquet rồi upload lên Google Drive/Dropbox
"""

from pyspark.sql import SparkSession
import os

print("="*60)
print("EXPORT ICEBERG TO PARQUET FOR SHARING")
print("="*60)

# Initialize Spark with Iceberg
spark = SparkSession.builder \
    .appName("Export Iceberg to Parquet") \
    .config("spark.jars.packages", "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0") \
    .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.local.type", "hadoop") \
    .config("spark.sql.catalog.local.warehouse", "D:/Bigdata/iceberg-warehouse") \
    .getOrCreate()

print("\n✅ SparkSession initialized!")

# Read from Iceberg
print("\n📖 Reading from Iceberg table: stock_db.stock_bronze")
df = spark.table("local.stock_db.stock_bronze")

# Show sample data
print("\n📊 Sample data:")
df.show(5, truncate=False)

# Count records
record_count = df.count()
print(f"\n📈 Total records: {record_count}")

# Export path
export_path = "D:/Bigdata/export/stock_bronze_parquet"

# Create export directory if not exists
os.makedirs("D:/Bigdata/export", exist_ok=True)

# Export to Parquet
print(f"\n💾 Exporting to Parquet: {export_path}")
df.write.mode("overwrite").parquet(export_path)

print("\n" + "="*60)
print("✅ EXPORT COMPLETED!")
print("="*60)
print(f"\n📁 Exported to: {export_path}")
print(f"📊 Total records: {record_count}")

# Check file size
import glob
parquet_files = glob.glob(f"{export_path}/*.parquet")
total_size = sum(os.path.getsize(f) for f in parquet_files)
print(f"💾 Total size: {total_size / (1024*1024):.2f} MB")

print("\n" + "="*60)
print("📤 NEXT STEPS TO SHARE:")
print("="*60)
print("1. Nén folder: D:/Bigdata/export/stock_bronze_parquet")
print("2. Upload lên Google Drive hoặc Dropbox")
print("3. Share link download với người khác")
print("\n4. Người khác đọc bằng:")
print("   df = spark.read.parquet('path/to/stock_bronze_parquet')")
print("   df.show()")
print("="*60)

spark.stop()
