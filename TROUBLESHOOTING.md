# Troubleshooting Guide

## Common Issues and Solutions

### 1. Containers Won't Start

#### Problem: `Error starting userland proxy`

```
Error response from daemon: driver failed programming external connectivity on endpoint...
```

**Solution**: Port is already in use

```bash
# Check what's using the port (e.g., 9092)
netstat -ano | findstr :9092

# Stop the process or change port in docker-compose.yml
# Then restart
docker compose down
docker compose up -d
```

#### Problem: `no configuration file provided: not found`

**Solution**: Make sure you're in the project root directory

```bash
cd D:\bigdata-stock-market-analysis
docker compose up -d
```

---

### 2. Kafka Issues

#### Problem: Producer can't connect to Kafka

```
KafkaConnectionError: Connection error
```

**Solutions**:

```bash
# 1. Check Kafka is running and healthy
docker compose ps kafka

# 2. Check Kafka logs
docker compose logs kafka

# 3. Verify Kafka is listening
docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092

# 4. Wait for Kafka to be ready (can take 30-60 seconds on first start)
```

#### Problem: Topic doesn't exist

```
Unknown topic or partition
```

**Solution**: Create the topic

```bash
docker exec kafka kafka-topics --create \
  --if-not-exists \
  --bootstrap-server localhost:9092 \
  --topic stock_ticks \
  --partitions 1 \
  --replication-factor 1
```

---

### 3. MinIO Issues

#### Problem: Can't access MinIO Console

```
This site can't be reached
```

**Solutions**:

```bash
# 1. Check MinIO is running
docker compose ps minio

# 2. Check MinIO logs
docker compose logs minio

# 3. Verify ports are exposed
docker port minio
```

#### Problem: Bucket doesn't exist

```
The specified bucket does not exist
```

**Solution**: Create bucket manually

```bash
docker run --rm --network bigdata-stock-market-analysis_default \
  --entrypoint sh minio/mc -c "\
  mc alias set myminio http://minio:9000 minioadmin minioadmin && \
  mc mb myminio/warehouse --ignore-existing && \
  mc ls myminio/"
```

#### Problem: S3 Access Denied

```
com.amazonaws.services.s3.model.AmazonS3Exception: Access Denied
```

**Solution**: Verify credentials in environment variables

```bash
# Check spark-app environment
docker exec spark-streaming env | grep MINIO

# Should show:
# MINIO_ACCESS_KEY=minioadmin
# MINIO_SECRET_KEY=minioadmin
```

---

### 4. Spark Issues

#### Problem: Spark can't write to Iceberg

```
org.apache.iceberg.exceptions.CommitFailedException
```

**Solutions**:

```bash
# 1. Check MinIO is accessible from Spark
docker exec spark-streaming curl -I http://minio:9000

# 2. Verify warehouse bucket exists
docker run --rm --network bigdata-stock-market-analysis_default \
  minio/mc ls myminio/warehouse --config-dir=/tmp

# 3. Check Spark logs for detailed errors
docker compose logs spark-app | grep -i error

# 4. Restart Spark app
docker compose restart spark-app
```

#### Problem: Checkpoint location error

```
java.io.IOException: Failed to create checkpoint directory
```

**Solution**: Clear checkpoints and restart

```bash
docker compose down
docker volume rm bigdata-stock-market-analysis_spark_checkpoints
docker compose up -d
```

#### Problem: ClassNotFoundException for S3AFileSystem

```
java.lang.ClassNotFoundException: org.apache.hadoop.fs.s3a.S3AFileSystem
```

**Solution**: Rebuild Spark image (AWS JARs missing)

```bash
docker compose build --no-cache spark-app
docker compose up -d spark-app
```

---

### 5. Producer Issues

#### Problem: Yahoo Finance API errors

```
HTTPError: 404 Client Error
```

**Solutions**:

```bash
# 1. Check if stock symbol is valid
# Some symbols may be delisted or incorrect

# 2. Check Yahoo Finance website directly
# https://finance.yahoo.com/quote/AAPL

# 3. Update stock symbols in yahoo_to_kafka.py
# Edit raw_data_bronze/yahoo_to_kafka.py

# 4. Rebuild producer
docker compose build producer
docker compose restart producer
```

#### Problem: Too many requests / Rate limiting

```
HTTPError: 429 Too Many Requests
```

**Solution**: Increase sleep time between fetches

```python
# Edit raw_data_bronze/yahoo_to_kafka.py
SLEEP_TIME = 60  # Change from 30 to 60 seconds
```

```bash
docker compose restart producer
```

---

### 6. Network Issues

#### Problem: Services can't communicate

```
Network bigdata-stock-market-analysis_default not found
```

**Solution**: Recreate network

```bash
docker compose down
docker network prune
docker compose up -d
```

#### Problem: DNS resolution fails

```
Could not resolve host: kafka
```

**Solution**: Services are not on same network

```bash
# Check networks
docker network ls

# Inspect network
docker network inspect bigdata-stock-market-analysis_default

# All services should be listed. If not, recreate:
docker compose down
docker compose up -d
```

---

### 7. Data/Volume Issues

#### Problem: No data showing in MinIO

```
Bucket is empty
```

**Solutions**:

```bash
# 1. Check if producer is running
docker compose logs producer | tail -20

# 2. Check if data is in Kafka
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic stock_ticks \
  --from-beginning \
  --max-messages 5

# 3. Check Spark is consuming
docker compose logs spark-app | grep "Streaming to Iceberg"

# 4. If everything runs but no data, wait 2-3 minutes
# First batch takes time to write
```

#### Problem: Want to start fresh

```
Old data causing issues
```

**Solution**: Clean everything

```bash
# Stop and remove all containers and volumes
docker compose down -v

# Remove images (optional, forces rebuild)
docker compose down --rmi all

# Start fresh
docker compose up -d --build
```

---

### 8. Build Issues

#### Problem: Docker build fails

```
ERROR [internal] load metadata for docker.io/...
```

**Solution**: Check Docker Hub connection

```bash
# Test connection
docker pull hello-world

# Login to Docker Hub if needed
docker login

# Retry build
docker compose build --no-cache
```

#### Problem: Out of disk space

```
no space left on device
```

**Solution**: Clean up Docker

```bash
# Remove unused images, containers, networks
docker system prune -a --volumes

# Check disk usage
docker system df
```

---

## Diagnostic Commands

### Check Everything

```bash
# Service status
docker compose ps

# All logs
docker compose logs --tail=50

# Resource usage
docker stats --no-stream

# Network connectivity
docker network inspect bigdata-stock-market-analysis_default
```

### Per-Service Diagnostics

#### Kafka

```bash
# List topics
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Describe topic
docker exec kafka kafka-topics --describe --topic stock_ticks --bootstrap-server localhost:9092

# Consume messages
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic stock_ticks \
  --from-beginning \
  --max-messages 10
```

#### MinIO

```bash
# Check buckets
docker run --rm --network bigdata-stock-market-analysis_default \
  --entrypoint sh minio/mc -c "\
  mc alias set myminio http://minio:9000 minioadmin minioadmin && \
  mc ls myminio/"

# Check warehouse contents
docker run --rm --network bigdata-stock-market-analysis_default \
  --entrypoint sh minio/mc -c "\
  mc alias set myminio http://minio:9000 minioadmin minioadmin && \
  mc ls myminio/warehouse/ --recursive"
```

#### Spark

```bash
# Check environment
docker exec spark-streaming env | grep -E "KAFKA|MINIO|ICEBERG"

# Test network connectivity
docker exec spark-streaming ping -c 3 kafka
docker exec spark-streaming ping -c 3 minio

# Check if app is running
docker exec spark-streaming ps aux | grep spark
```

#### Producer

```bash
# Check logs for errors
docker compose logs producer | grep -i error

# Check environment
docker exec stock-producer env | grep KAFKA

# Test Kafka connectivity
docker exec stock-producer python -c "from kafka import KafkaProducer; print(KafkaProducer(bootstrap_servers='kafka:29092'))"
```

---

## Performance Tuning

### Kafka

```yaml
# In docker-compose.yml, add under kafka environment:
KAFKA_NUM_NETWORK_THREADS: 8
KAFKA_NUM_IO_THREADS: 8
KAFKA_SOCKET_SEND_BUFFER_BYTES: 102400
KAFKA_SOCKET_RECEIVE_BUFFER_BYTES: 102400
```

### Spark

```yaml
# In docker-compose.yml, add under spark-app environment:
SPARK_EXECUTOR_MEMORY: 2g
SPARK_DRIVER_MEMORY: 1g
SPARK_EXECUTOR_CORES: 2
```

### MinIO

```yaml
# Add to minio service:
environment:
  MINIO_STORAGE_CLASS_STANDARD: "EC:2"
  MINIO_COMPRESS: "on"
```

---

## Getting Help

If you're still stuck:

1. **Collect logs**:

```bash
docker compose logs > debug.log
```

2. **Check service status**:

```bash
docker compose ps > status.txt
```

3. **Check configurations**:

```bash
docker compose config > config.yml
```

4. **Share these files** when asking for help

---

## Emergency Reset

If nothing works, nuclear option:

```bash
# Stop everything
docker compose down -v

# Remove all related containers
docker ps -a | grep bigdata | awk '{print $1}' | xargs docker rm -f

# Remove all related images
docker images | grep -E "bigdata|spark|kafka|minio" | awk '{print $3}' | xargs docker rmi -f

# Clean Docker system
docker system prune -af --volumes

# Start from scratch
cd D:\bigdata-stock-market-analysis
docker compose up -d --build
```
