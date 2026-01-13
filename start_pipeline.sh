#!/bin/bash
# Bash script to start all pipeline components
# Run this from the project root directory

echo "================================================================================"
echo "  Real-time Stock Market Analytics Pipeline"
echo "  Starting all components..."
echo "================================================================================"
echo ""

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "ERROR: Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

echo "[1/6] Checking Docker services..."
docker compose ps

echo ""
echo "[2/6] Starting Kafka and MinIO (if not already running)..."
docker compose up -d

echo ""
echo "[3/6] Waiting for services to be ready (10 seconds)..."
sleep 10

echo ""
echo "[4/6] Creating Kafka topic (if not exists)..."
docker exec kafka kafka-topics --create \
  --if-not-exists \
  --bootstrap-server localhost:9092 \
  --topic stock_ticks \
  --partitions 1 \
  --replication-factor 1

echo ""
echo "[5/6] Setting environment variables..."
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export MINIO_ENDPOINT="http://localhost:9000"
export MINIO_ACCESS_KEY="minioadmin"
export MINIO_SECRET_KEY="minioadmin"
export ICEBERG_WAREHOUSE="s3a://warehouse"

echo ""
echo "[6/6] Starting Python components..."
echo ""
echo "================================================================================"
echo "  Please run each command in a separate terminal:"
echo "================================================================================"
echo ""
echo "Terminal 1 - Producer:"
echo "  cd raw_data_bronze && python yahoo_to_kafka.py"
echo ""
echo "Terminal 1 - Kafka to Spark:"
echo "  cd raw_data_bronze && python kafka_to_spark.py"
echo ""
echo "Terminal 2 - Bronze Layer:"
echo "  cd raw_data_bronze && python spark_to_iceberg_bronze.py"
echo ""
echo "Terminal 3 - Silver Layer:"
echo "  cd processed_data_silver && python bronze_to_silver.py"
echo ""
echo "Terminal 4 - Gold Layer:"
echo "  cd processed_data_gold && python silver_to_gold_streaming.py"
echo ""
echo "Terminal 5 - Dashboard:"
echo "  cd processed_data_gold && streamlit run dashboard.py"
echo ""
echo "================================================================================"
echo "  Dashboard will open at: http://localhost:8501"
echo "  MinIO Console: http://localhost:9001"
echo ""
echo "  Wait 1-2 minutes for data to flow through all layers."
echo "  To check pipeline status: python check_pipeline_status.py"
echo "================================================================================"
