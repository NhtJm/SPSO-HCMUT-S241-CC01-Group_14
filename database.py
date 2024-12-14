from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

def connect_to_database():
    if not MONGO_URI or not DATABASE_NAME:
        raise ValueError("Missing MongoDB connection details in .env file")
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    print(f"Connected to MongoDB database: {DATABASE_NAME}")
    return db
