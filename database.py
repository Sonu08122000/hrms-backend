import os
from pymongo import MongoClient, ASCENDING
from pymongo.database import Database

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://saurabh73:sOajKS0HZ2wJaQXm@database.6z5uhhu.mongodb.net/hrms_lite?retryWrites=true&w=majority")
DB_NAME = os.getenv("DB_NAME", "hrms_lite")

client: MongoClient = MongoClient(MONGO_URI)
db: Database = client[DB_NAME]

# Collections
employees_collection = db["employees"]
attendance_collection = db["attendance"]

# Indexes — enforce uniqueness and speed up queries
employees_collection.create_index("employee_id", unique=True)
employees_collection.create_index([("email", ASCENDING)], unique=True)
attendance_collection.create_index(
    [("employee_id", ASCENDING), ("date", ASCENDING)], unique=True
)


def get_db() -> Database:
    return db
