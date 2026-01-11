"""
Phase 5: Verify & Ban giao
Query Iceberg Bronze Table de verify pipeline hoat dong
"""

from pyspark.sql import SparkSession

# Khoi tao SparkSession voi Iceberg support
spark = (
    SparkSession.builder
    .appName("Phase5-Verify-Iceberg-Bronze")
    .master("local[*]")
    .config("spark.jars.packages", "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0")
    .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.local.type", "hadoop")
    .config("spark.sql.catalog.local.warehouse", "D:/Bigdata/iceberg-warehouse")
    .config("spark.sql.defaultCatalog", "local")
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print("=" * 80)
print("PHASE 5: VERIFY & BAN GIAO")
print("=" * 80)

# 1. Kiem tra bang ton tai
print("\n" + "=" * 80)
print("1. VERIFY: Bang stock_bronze ton tai")
print("=" * 80)
spark.sql("SHOW TABLES IN stock_db").show()

# 2. Kiem tra schema
print("\n" + "=" * 80)
print("2. VERIFY: Schema cua bang stock_bronze")
print("=" * 80)
spark.sql("DESCRIBE stock_db.stock_bronze").show(truncate=False)

# 3. Dem so luong records
print("\n" + "=" * 80)
print("3. VERIFY: So luong records")
print("=" * 80)
count_df = spark.sql("SELECT COUNT(*) as total_records FROM stock_db.stock_bronze")
count_df.show()
total = count_df.collect()[0]['total_records']
print(f"   >>> Total records: {total}")

# 4. QUERY CHINH - Theo yeu cau Phase 5
print("\n" + "=" * 80)
print("4. VERIFY: Query chinh theo yeu cau")
print("   SELECT symbol, close, volume, event_time")
print("   FROM stock_bronze")
print("   ORDER BY ingest_time DESC")
print("   LIMIT 10;")
print("=" * 80)
spark.sql("""
SELECT symbol, close, volume, event_time
FROM stock_db.stock_bronze
ORDER BY ingest_time DESC
LIMIT 10
""").show(truncate=False)

# 5. Kiem tra du lieu tang theo thoi gian
print("\n" + "=" * 80)
print("5. VERIFY: Du lieu tang theo thoi gian (group by minute)")
print("=" * 80)
spark.sql("""
SELECT 
  DATE_FORMAT(ingest_time, 'yyyy-MM-dd HH:mm') as minute,
  COUNT(*) as records
FROM stock_db.stock_bronze
GROUP BY DATE_FORMAT(ingest_time, 'yyyy-MM-dd HH:mm')
ORDER BY minute DESC
LIMIT 10
""").show(truncate=False)

# 6. Thong ke theo sector
print("\n" + "=" * 80)
print("6. BONUS: Thong ke theo sector")
print("=" * 80)
spark.sql("""
SELECT 
  sector, 
  COUNT(*) as count, 
  ROUND(AVG(close), 2) as avg_close,
  ROUND(MIN(close), 2) as min_close,
  ROUND(MAX(close), 2) as max_close
FROM stock_db.stock_bronze
GROUP BY sector
ORDER BY count DESC
""").show()

# 7. Thong ke theo symbol
print("\n" + "=" * 80)
print("7. BONUS: Top 10 symbols theo so luong records")
print("=" * 80)
spark.sql("""
SELECT 
  symbol, 
  sector,
  COUNT(*) as count,
  ROUND(AVG(close), 2) as avg_price
FROM stock_db.stock_bronze
GROUP BY symbol, sector
ORDER BY count DESC
LIMIT 10
""").show()

# KET LUAN
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)

if total > 0:
    print(f"""
    PASS: Bang stock_bronze TON TAI
    PASS: Co {total} records trong bang
    PASS: Du lieu co day du cot (symbol, close, volume, event_time)
    PASS: Co the query bang Spark SQL
    
    PHASE 5 HOAN THANH! Pipeline hoat dong tot!
    """)
else:
    print(f"""
        WARNING: Bang stock_bronze TRONG (0 records)
    
    Kiem tra:
    1. Producer (yahoo_to_kafka.py) co dang chay khong?
    2. Iceberg writer (spark_to_iceberg_bronze.py) co dang chay khong?
    3. Kafka container co dang chay khong?
    
    Thu lai sau vai phut khi pipeline da chay.
    """)

print("=" * 80)

spark.stop()
