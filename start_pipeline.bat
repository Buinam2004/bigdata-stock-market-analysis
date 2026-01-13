@echo off
REM Windows batch script to start all pipeline components
REM Run this from the project root directory

echo ================================================================================
echo   Real-time Stock Market Analytics Pipeline
echo   Starting all components...
echo ================================================================================
echo.

REM Check if Docker is running
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [1/6] Checking Docker services...
docker compose ps

echo.
echo [2/6] Starting Kafka and MinIO (if not already running)...
docker compose up -d

echo.
echo [3/6] Waiting for services to be ready (10 seconds)...
timeout /t 10 /nobreak >nul

echo.
echo [4/6] Creating Kafka topic (if not exists)...
docker exec kafka kafka-topics --create --if-not-exists --bootstrap-server localhost:9092 --topic stock_ticks --partitions 1 --replication-factor 1

echo.
echo [5/6] Setting environment variables...
set KAFKA_BOOTSTRAP_SERVERS=localhost:9092
set MINIO_ENDPOINT=http://localhost:9000
set MINIO_ACCESS_KEY=minioadmin
set MINIO_SECRET_KEY=minioadmin
set ICEBERG_WAREHOUSE=s3a://warehouse

echo.
echo [6/6] Starting Python components in separate windows...
echo.

REM Start each component in a new window
start "Producer - Yahoo to Kafka" cmd /k "cd raw_data_bronze && python yahoo_to_kafka.py"
timeout /t 3 /nobreak >nul

start "Producer - Kafka to Spark" cmd /k "cd raw_data_bronze && python kafka_to_spark.py"
timeout /t 3 /nobreak >nul

start "Bronze Layer - Spark to Iceberg" cmd /k "cd raw_data_bronze && python spark_to_iceberg_bronze.py"
timeout /t 3 /nobreak >nul

start "Silver Layer - Data Quality" cmd /k "cd processed_data_silver && python bronze_to_silver.py"
timeout /t 3 /nobreak >nul

start "Gold Layer - Technical Indicators" cmd /k "cd processed_data_gold && python silver_to_gold_streaming.py"
timeout /t 3 /nobreak >nul

start "Dashboard - Streamlit UI" cmd /k "cd processed_data_gold && streamlit run dashboard.py"

echo.
echo ================================================================================
echo   All components are starting!
echo ================================================================================
echo.
echo   5 new windows have been opened:
echo   1. Producer (Yahoo Finance ^-^> Kafka)
echo   2. Bronze Layer (Raw Data Ingestion)
echo   3. Silver Layer (Data Quality)
echo   4. Gold Layer (Technical Indicators)
echo   5. Dashboard (Streamlit UI)
echo.
echo   Dashboard will open at: http://localhost:8501
echo   MinIO Console: http://localhost:9001
echo.
echo   Wait 1-2 minutes for data to flow through all layers.
echo   Use Ctrl+C in each window to stop components.
echo.
echo   To check pipeline status: python check_pipeline_status.py
echo ================================================================================
pause
