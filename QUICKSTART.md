# Quick Start Guide

## 🚀 Start the Pipeline (Kafka/MinIO in Docker, code on host)

```bash
# 1. Start infrastructure
docker compose up -d

# 2. Wait for services to be healthy (30-60 seconds)
docker compose ps

# 3. Create Kafka topic
docker exec kafka kafka-topics --create \
  --if-not-exists \
  --bootstrap-server localhost:9092 \
  --topic stock_ticks \
  --partitions 1 \
  --replication-factor 1

# 4. Set env vars (PowerShell)
$env:KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
$env:KAFKA_TOPIC="stock_ticks"
$env:MINIO_ENDPOINT="http://localhost:9000"
$env:MINIO_ACCESS_KEY="minioadmin"
$env:MINIO_SECRET_KEY="minioadmin"
$env:ICEBERG_WAREHOUSE="s3a://warehouse"

# 5. Install deps (first run)
cd raw_data_bronze
pip install -r requirements.txt

# 6. Run producer locally
python yahoo_to_kafka.py

# 7. Run Spark streaming locally (new terminal)
cd raw_data_bronze
spark-submit \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.7,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.367 \
  spark_to_iceberg_bronze.py

# 8. Query Iceberg locally (optional, new terminal)
cd raw_data_bronze
spark-submit \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.367 \
  query_iceberg_bronze.py
```

## 📊 Verify Data

### Check MinIO Console

1. Open http://localhost:9001
2. Login: `minioadmin` / `minioadmin`
3. Navigate to `warehouse` bucket
4. You should see `stock_db/stock_bronze/` folders appearing

### Query Iceberg Data

Use your local Spark install; see step 8 above.

## 🔍 Service URLs

- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Kafka**: localhost:9092
- **MinIO API**: http://localhost:9000

## 🛠️ Useful Commands

### Check service status

```bash
docker compose ps
```

### View logs

```bash
# Infrastructure
docker compose logs -f

# Kafka only
docker compose logs -f kafka
```

### Restart specific service

```bash
docker compose restart kafka
docker compose restart minio
```

### Stop everything

```bash
docker compose down

# Stop and remove volumes (data will be lost)
docker compose down -v
```

### Rebuild after code changes

No rebuild needed; code runs on host. Restart Spark submit if you change Python files.

## 🐛 Troubleshooting

### Producer not sending data

```bash
# Check producer logs
docker compose logs producer

# Verify Kafka topic exists
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Check if messages are in Kafka
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic stock_ticks \
  --from-beginning \
  --max-messages 5
```

### Spark not writing to Iceberg

```bash
# Check Spark logs
docker compose logs spark-app

# Verify MinIO bucket exists
docker run --rm --network bigdata-stock-market-analysis_default \
  --entrypoint sh minio/mc -c "\
  mc alias set myminio http://minio:9000 minioadmin minioadmin && \
  mc ls myminio/warehouse"
```

### Reset everything

```bash
# Stop and remove all data
docker compose down -v

# Remove old images
docker compose build --no-cache

# Start fresh
docker compose up -d --build
```

## 📝 Development Workflow

1. Make code changes in `raw_data_bronze/`
2. Rerun `spark-submit ... spark_to_iceberg_bronze.py` from your host
3. Query with `query_iceberg_bronze.py`
