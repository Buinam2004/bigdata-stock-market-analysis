# Real-time Stock Data Pipeline with Apache Iceberg

Dự án xử lý dữ liệu chứng khoán theo thời gian thực sử dụng Kafka, Spark Streaming và Apache Iceberg.

## Kiến trúc

```
Yahoo Finance API -> Kafka -> Spark Streaming -> Iceberg (Bronze Layer)
```

## Yêu cầu

- Python 3.8+
- Apache Kafka
- Apache Spark 3.x
- Docker & Docker Compose

## Cài đặt

1. Clone repository:

```bash
git clone <your-repo-url>
cd Bigdata
```

2. Cài đặt các thư viện Python:

```bash
pip install -r requirements.txt
```

3. Khởi động các dịch vụ với Docker Compose:

```bash
docker-compose up -d
```

## Các file chính

- `yahoo_to_kafka.py`: Lấy dữ liệu từ Yahoo Finance và gửi vào Kafka
- `kafka_to_spark.py`: Đọc dữ liệu từ Kafka và xử lý với Spark Streaming
- `spark_to_iceberg_bronze.py`: Ghi dữ liệu vào Iceberg Bronze layer
- `query_iceberg_bronze.py`: Truy vấn dữ liệu từ Iceberg
- `export_to_parquet.py`: Export dữ liệu ra Parquet
- `read_shared_parquet.py`: Đọc dữ liệu Parquet

## Sử dụng

1. Chạy producer để lấy dữ liệu:

```bash
python yahoo_to_kafka.py
```

2. Chạy Spark Streaming để xử lý:

```bash
python spark_to_iceberg_bronze.py
```

3. Truy vấn dữ liệu:

```bash
python query_iceberg_bronze.py
```

## Cấu trúc dữ liệu

Dữ liệu được lưu trữ theo cấu trúc Bronze-Silver-Gold trong Iceberg warehouse.

## Lưu ý

- Các thư mục `checkpoints/`, `iceberg-warehouse/`, và `spark-warehouse/` sẽ được tạo tự động khi chạy
- Đảm bảo Kafka và Spark đang chạy trước khi thực thi các script Python
