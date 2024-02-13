import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()


client = MongoClient(os.getenv("MONGODB_CONNECTION_URL"))
db = client[os.getenv("DB_NAME")]
collection_name = db[os.getenv("COLLECTION_NAME")]
user_collection = db[os.getenv("USER_COLLECTION")]
