"""
Script để đọc Parquet files đã được share
Người nhận dùng script này để đọc dữ liệu
"""

from pyspark.sql import SparkSession

# Đường dẫn đến folder Parquet (thay đổi theo vị trí tải về)
PARQUET_PATH = "D:/Download/stock_bronze_parquet"  # Sửa path này

print("="*60)
print("READ SHARED PARQUET DATA")
print("="*60)

# Initialize Spark
spark = SparkSession.builder \
    .appName("Read Shared Parquet") \
    .getOrCreate()

print(f"\n📖 Reading Parquet from: {PARQUET_PATH}")

# Read Parquet
df = spark.read.parquet(PARQUET_PATH)

print("\n📊 Schema:")
df.printSchema()

print("\n📈 Total records:", df.count())

print("\n🔍 Sample data:")
df.show(10, truncate=False)

print("\n📊 Records by sector:")
df.groupBy("sector").count().orderBy("count", ascending=False).show()

print("\n📊 Latest 10 records:")
df.orderBy("ingest_time", ascending=False).show(10, truncate=False)

print("\n✅ Data loaded successfully!")
print("="*60)

# Keep Spark session open for interactive queries
print("\nSpark session is ready. You can run queries like:")
print("  df.filter(df.symbol == 'AAPL').show()")
print("  df.groupBy('sector').agg({'close': 'avg'}).show()")

# Uncomment to stop Spark when done
# spark.stop()
