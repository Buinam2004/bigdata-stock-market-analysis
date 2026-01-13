# Bigdata Stock Market Analysis

Real-time stock data pipeline using Kafka, Spark Streaming, Apache Iceberg, and MinIO.

## Architecture

```
Yahoo Finance API → Kafka → Spark Streaming → Iceberg (Bronze Layer) → MinIO (S3)
```

## Tech Stack

- **Kafka (KRaft mode)**: Message streaming (no ZooKeeper)
- **Apache Spark**: Stream processing
- **Apache Iceberg**: Data lakehouse table format
- **MinIO**: S3-compatible object storage
- **Python**: Data ingestion and processing

## Quick Start

### 1. Start infrastructure (Kafka + MinIO) with Docker Compose

```bash
docker compose up -d
```

This starts only the infrastructure:

- **MinIO** on ports 9000 (API) and 9001 (Console)
- **Kafka** on port 9092 (KRaft mode, no ZooKeeper)
- **Bucket init** via `minio-init`

### 2. Access Services

- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Kafka**: localhost:9092

### 3. Create Kafka Topic

```bash
docker exec kafka kafka-topics --create \
  --if-not-exists \
  --bootstrap-server localhost:9092 \
  --topic stock_ticks \
  --partitions 1 \
  --replication-factor 1
```

### 4. Verify Data in MinIO

1. Open MinIO Console at http://localhost:9001
2. Login with `minioadmin` / `minioadmin`
3. Check the `warehouse` bucket for Iceberg data

### 5. Run the pipeline locally (no containers for code)

1) Copy env vars and install deps

```bash
cp .env.example .env
cd raw_data_bronze
pip install -r requirements.txt
```

2) Export env vars

```bash
# PowerShell
$env:KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
$env:KAFKA_TOPIC="stock_ticks"
$env:MINIO_ENDPOINT="http://localhost:9000"
$env:MINIO_ACCESS_KEY="minioadmin"
$env:MINIO_SECRET_KEY="minioadmin"
$env:ICEBERG_WAREHOUSE="s3a://warehouse"

# Optional: checkpoint dir
$env:CHECKPOINT_LOCATION="./checkpoints/iceberg_bronze"
```

3) Run producer locally

```bash
cd raw_data_bronze
python yahoo_to_kafka.py
```

4) Run Spark streaming locally (new terminal)

```bash
cd raw_data_bronze
spark-submit \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.7,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.367 \
  --conf spark.hadoop.fs.s3a.endpoint=http://localhost:9000 \
  --conf spark.hadoop.fs.s3a.access.key=minioadmin \
  --conf spark.hadoop.fs.s3a.secret.key=minioadmin \
  --conf spark.hadoop.fs.s3a.path.style.access=true \
  --conf spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem \
  --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false \
  spark_to_iceberg_bronze.py
```

5) Query Iceberg locally (new terminal)

```bash
cd raw_data_bronze
spark-submit \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.367 \
  query_iceberg_bronze.py
```

## Project Structure

```
.
├── docker-compose.yml              # Service orchestration
├── docker/
│   ├── producer/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── spark/
│       └── Dockerfile
├── raw_data_bronze/
│   ├── yahoo_to_kafka.py          # Producer: Yahoo Finance → Kafka
│   ├── kafka_to_spark.py          # Test: Kafka → Spark console
│   ├── spark_to_iceberg_bronze.py # Main: Spark → Iceberg → MinIO
│   ├── query_iceberg_bronze.py    # Query Iceberg tables
│   └── requirements.txt
└── .env.example                    # Environment variables template
```

## Development

Develop and run everything locally; Docker is used only for Kafka/MinIO. Follow the Quick Start section to set env vars, install deps, and run `yahoo_to_kafka.py` and `spark_to_iceberg_bronze.py` directly from your machine.

## Key Changes from Original Setup

✅ **Removed ZooKeeper** - Kafka now runs in KRaft mode  
✅ **Removed Hadoop dependency** - Using MinIO S3 instead of local HDFS  
✅ **Docker for infra only** - Kafka/MinIO in containers; code runs locally  
✅ **Spark on host** - Use your local Spark install (3.5.7)  
✅ **S3-compatible storage** - Iceberg data stored in MinIO  
✅ **Environment variables** - Easy configuration for Docker and local dev

## Troubleshooting

### View logs

```bash
# Infrastructure services
docker compose logs -f

# Kafka only
docker compose logs -f kafka
```

### Restart services

```bash
docker compose restart kafka
docker compose restart minio
```

### Clean up and restart

```bash
docker compose down -v
docker compose up -d
```

### Initialize MinIO bucket manually

If the warehouse bucket doesn't exist:

```bash
docker run --rm --network bigdata-stock-market-analysis_default \
  --entrypoint sh minio/mc -c "\
  mc alias set myminio http://minio:9000 minioadmin minioadmin && \
  mc mb myminio/warehouse --ignore-existing"
```

## Data Flow

1. **Producer** (`yahoo_to_kafka.py`) fetches stock prices from Yahoo Finance every 30 seconds
2. **Kafka** receives and stores messages in the `stock_ticks` topic
3. **Spark Streaming** (`spark_to_iceberg_bronze.py`) consumes from Kafka and writes to Iceberg
4. **Iceberg** stores data in Bronze layer with schema and time-travel capabilities
5. **MinIO** provides S3-compatible object storage for Iceberg data files

## Stop Services

```bash
docker compose down

# To also remove volumes (data will be lost)
docker compose down -v
```
