from pymongo import MongoClient
from kafka import KafkaProducer
import json

# ================= CONFIG =================

MONGO_URI = "mongodb+srv://20225211:20225211@cluster0.ejcendu.mongodb.net/?appName=Cluster0"
DB_NAME = "stock_streaming"
COLLECTION_NAME = "stock_prices"

KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "stock-trades-stream"

# ==========================================

# MongoDB client
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

# Kafka producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

print("Listening MongoDB Change Stream...")

# Listen to MongoDB Change Stream (INSERT only)
with collection.watch([{"$match": {"operationType": "insert"}}]) as stream:
    for change in stream:
        document = change["fullDocument"]

        # Remove _id (Spark không cần)
        if "_id" in document:
            document.pop("_id")

        producer.send(KAFKA_TOPIC, document)
        producer.flush()

        print(
            f"Sent to Kafka: {document.get('symbol')} "
            f"@ {document.get('timestamp')}"
        )
