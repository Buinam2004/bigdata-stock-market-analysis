"""
Pipeline Status Checker
Quickly check the status of all layers in the pipeline
"""

import os
from pyspark.sql import SparkSession

# Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
ICEBERG_WAREHOUSE = os.getenv("ICEBERG_WAREHOUSE", "s3a://warehouse")

# Initialize Spark
spark = (
    SparkSession.builder.appName("Pipeline-Status-Check")
    .master("local[2]")
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
    .config("spark.ui.enabled", "false")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

print("=" * 80)
print("🔍 PIPELINE STATUS CHECK")
print("=" * 80)

try:
    spark.sql("USE stock_db")

    # Check Bronze Layer
    print("\n🥉 BRONZE LAYER (Raw Data)")
    print("-" * 80)
    try:
        bronze_df = spark.read.format("iceberg").table("stock_bronze")
        bronze_count = bronze_df.count()
        latest_bronze = bronze_df.orderBy(bronze_df.ingest_time.desc()).first()

        print(f"  ✅ Status: ACTIVE")
        print(f"  📊 Total Records: {bronze_count:,}")
        if latest_bronze:
            print(f"  🕐 Latest Record: {latest_bronze['ingest_time']}")
            print(
                f"  📈 Sample Symbol: {latest_bronze['symbol']} @ ${latest_bronze['close']}"
            )
    except Exception as e:
        print(f"  ❌ Status: NO DATA or ERROR")
        print(f"  ⚠️  Error: {str(e)[:100]}")

    # Check Silver Layer
    print("\n🥈 SILVER LAYER (Cleansed Data)")
    print("-" * 80)
    try:
        silver_df = spark.read.format("iceberg").table("stock_silver")
        silver_count = silver_df.count()
        latest_silver = silver_df.orderBy(silver_df.processed_time.desc()).first()

        # Calculate quality metrics
        valid_prices = silver_df.filter(silver_df.is_valid_price == True).count()
        anomalies = silver_df.filter(silver_df.has_anomaly == True).count()

        print(f"  ✅ Status: ACTIVE")
        print(f"  📊 Total Records: {silver_count:,}")
        print(
            f"  ✔️  Valid Prices: {valid_prices:,} ({valid_prices/silver_count*100:.1f}%)"
        )
        print(f"  ⚠️  Anomalies: {anomalies} ({anomalies/silver_count*100:.2f}%)")
        if latest_silver:
            print(f"  🕐 Latest Record: {latest_silver['processed_time']}")
    except Exception as e:
        print(f"  ❌ Status: NO DATA or ERROR")
        print(f"  ⚠️  Error: {str(e)[:100]}")

    # Check Gold Layer
    print("\n🥇 GOLD LAYER (Analytics & Indicators)")
    print("-" * 80)
    try:
        gold_df = spark.read.format("iceberg").table("stock_gold_realtime")
        gold_count = gold_df.count()

        # Get latest per symbol
        latest_gold = spark.sql(
            """
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY event_time DESC) as rn
                FROM stock_gold_realtime
            ) WHERE rn = 1
        """
        )

        # Signal distribution
        signals = latest_gold.groupBy("recommendation").count().collect()
        signal_dict = {row["recommendation"]: row["count"] for row in signals}

        print(f"  ✅ Status: ACTIVE")
        print(f"  📊 Total Records: {gold_count:,}")
        print(f"  📈 Unique Symbols: {latest_gold.count()}")
        print(f"\n  🎯 Trading Signals:")
        for rec in ["STRONG BUY", "BUY", "HOLD", "SELL", "STRONG SELL"]:
            count = signal_dict.get(rec, 0)
            emoji = "🟢" if "BUY" in rec else "🔴" if "SELL" in rec else "🟡"
            print(f"     {emoji} {rec:12s}: {count}")

        # Latest update
        latest_record = gold_df.orderBy(gold_df.processed_time.desc()).first()
        if latest_record:
            print(f"\n  🕐 Latest Update: {latest_record['processed_time']}")

    except Exception as e:
        print(f"  ❌ Status: NO DATA or ERROR")
        print(f"  ⚠️  Error: {str(e)[:100]}")

    # Summary
    print("\n" + "=" * 80)
    print("📋 PIPELINE SUMMARY")
    print("=" * 80)

    try:
        bronze_ok = bronze_count > 0
        silver_ok = silver_count > 0
        gold_ok = gold_count > 0

        print(
            f"  Bronze → Silver: {'✅ FLOWING' if bronze_ok and silver_ok else '⚠️  CHECK LOGS'}"
        )
        print(
            f"  Silver → Gold:   {'✅ FLOWING' if silver_ok and gold_ok else '⚠️  CHECK LOGS'}"
        )
        print(f"  Gold → Dashboard: {'✅ READY' if gold_ok else '⚠️  WAITING FOR DATA'}")

        if bronze_ok and silver_ok and gold_ok:
            print(f"\n  🎉 All layers are operational!")
            print(f"  🚀 Dashboard should show data at http://localhost:8501")
        else:
            print(f"\n  ⚠️  Some layers need attention:")
            if not bronze_ok:
                print(
                    f"     • Start Bronze layer: python raw_data_bronze/spark_to_iceberg_bronze.py"
                )
            if not silver_ok:
                print(
                    f"     • Start Silver layer: python processed_data_silver/bronze_to_silver.py"
                )
            if not gold_ok:
                print(
                    f"     • Start Gold layer: python processed_data_gold/silver_to_gold_streaming.py"
                )

    except:
        print("  ⚠️  Unable to determine pipeline status")

except Exception as e:
    print(f"\n❌ ERROR: Could not connect to database")
    print(f"   {str(e)}")
    print(f"\n💡 Make sure:")
    print(f"   1. MinIO is running (docker compose up -d)")
    print(f"   2. Environment variables are set")
    print(f"   3. At least Bronze layer has run once")

print("\n" + "=" * 80)

spark.stop()
