# Migration Summary: Dockerized Setup with MinIO

## ✅ What Was Changed

### 1. **Removed ZooKeeper Dependency**

- Kafka now runs in **KRaft mode** (Kafka Raft)
- No separate ZooKeeper service needed
- Simpler architecture and faster startup

### 2. **Removed Hadoop Dependency**

- Replaced local Hadoop filesystem with **MinIO S3-compatible storage**
- Iceberg now uses S3A connector for object storage
- No need for `hadoop.home.dir` configuration

### 3. **Dockerized Development Environment**

- **Producer Service**: Python app that fetches Yahoo Finance data
- **Spark Service**: Uses official `apache/spark:3.5.4` image
- **MinIO Service**: S3-compatible object storage
- **Kafka Service**: Streaming platform in KRaft mode
- All services orchestrated with Docker Compose

### 4. **Environment Variable Configuration**

All Python scripts now read configuration from environment variables:

- `KAFKA_BOOTSTRAP_SERVERS`
- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `ICEBERG_WAREHOUSE`
- `CHECKPOINT_LOCATION`

## 📦 New Files Created

```
docker/
├── producer/
│   ├── Dockerfile              # Python producer image
│   └── requirements.txt        # Producer dependencies
├── spark/
│   └── Dockerfile              # Apache Spark with Iceberg + S3 support
└── init-minio.sh               # MinIO initialization script

Root:
├── .env.example                # Environment variables template
├── QUICKSTART.md               # Quick start guide
└── README.md                   # Updated documentation
```

## 📝 Modified Files

### Python Scripts

All scripts updated to:

- Read broker/storage config from environment variables
- Support both Docker and local execution
- Use MinIO S3 instead of local filesystem

**Modified:**

- `raw_data_bronze/yahoo_to_kafka.py`
- `raw_data_bronze/spark_to_iceberg_bronze.py`
- `raw_data_bronze/query_iceberg_bronze.py`
- `raw_data_bronze/kafka_to_spark.py`

### Configuration

- `docker-compose.yml` - Complete rewrite with 5 services
- `raw_data_bronze/EXECUTION_PLAN.md` - Updated for KRaft mode

## 🏗️ Architecture Comparison

### Before:

```
┌──────────────┐    ┌─────────┐    ┌───────────────┐
│   ZooKeeper  │───▶│  Kafka  │───▶│ Spark (local) │
└──────────────┘    └─────────┘    └───────────────┘
                                            │
                                            ▼
                                    ┌───────────────┐
                                    │ Local Hadoop  │
                                    │  Filesystem   │
                                    └───────────────┘
```

### After:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Producer   │───▶│ Kafka        │───▶│ Spark App    │
│   (Docker)   │    │ (KRaft mode) │    │ (Docker)     │
└──────────────┘    └──────────────┘    └──────────────┘
                                                │
                                                ▼
                                        ┌──────────────┐
                                        │    MinIO     │
                                        │ (S3-compat)  │
                                        └──────────────┘
```

## 🚀 Benefits

### 1. **Simplified Operations**

- One command to start everything: `docker compose up -d`
- No manual Spark/Hadoop installation needed
- Consistent environment across dev/prod

### 2. **Cloud-Ready**

- MinIO is S3-compatible (easy migration to AWS S3)
- Containerized apps deploy anywhere
- No local filesystem dependencies

### 3. **Modern Stack**

- Kafka KRaft (ZooKeeper-free)
- Official Apache Spark images
- Industry-standard object storage

### 4. **Developer Experience**

- Environment variables for all config
- Volume mounts for live code changes
- Health checks for proper startup order

## 🔄 Migration Steps for Existing Data

If you have data in the old `D:/Bigdata/iceberg-warehouse`:

### Option 1: Copy to MinIO (Recommended)

```bash
# 1. Start MinIO
docker compose up -d minio minio-init

# 2. Install MinIO client locally
# Windows: choco install minio-client
# Mac: brew install minio/stable/mc

# 3. Configure MinIO client
mc alias set local http://localhost:9000 minioadmin minioadmin

# 4. Copy existing data
mc mirror D:/Bigdata/iceberg-warehouse local/warehouse/
```

### Option 2: Start Fresh

```bash
# Just start everything - new data will be generated
docker compose up -d --build
```

## 📊 Verification Checklist

After starting services:

- [ ] All containers are running: `docker compose ps`
- [ ] MinIO Console accessible: http://localhost:9001
- [ ] Kafka topic created: `docker exec kafka kafka-topics --list --bootstrap-server localhost:9092`
- [ ] Producer sending data: `docker compose logs producer`
- [ ] Spark writing to Iceberg: `docker compose logs spark-app`
- [ ] Data in MinIO: Check `warehouse` bucket in console

## 🆘 Rollback Plan

If you need to go back to the old setup:

```bash
# 1. Stop new Docker environment
docker compose down -v

# 2. Your old scripts are still in raw_data_bronze/
#    They now support both modes via environment variables

# 3. Start old Kafka/ZooKeeper manually if needed
# 4. Unset environment variables to use localhost defaults
```

## 📚 Additional Resources

- [Kafka KRaft Documentation](https://kafka.apache.org/documentation/#kraft)
- [Apache Iceberg S3 Configuration](https://iceberg.apache.org/docs/latest/aws/)
- [MinIO Docker Documentation](https://min.io/docs/minio/container/index.html)
- [Apache Spark Docker Images](https://hub.docker.com/r/apache/spark)

## 🎯 Next Steps

1. **Test the pipeline**: `docker compose up -d --build`
2. **Monitor logs**: `docker compose logs -f`
3. **Query data**: See QUICKSTART.md
4. **Customize**: Edit environment variables in docker-compose.yml
5. **Scale**: Add more Kafka partitions, Spark workers, etc.
