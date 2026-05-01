from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "cinema_mongo_db")

client = MongoClient(MONGO_URL)
db = client[DATABASE_NAME]

users_collection = db["users"]
movies_collection = db["movies"]
screenings_collection = db["screenings"]
orders_collection = db["ticket_orders"]


def init_mongo_indexes():
    users_collection.create_index("email", unique=True)
    movies_collection.create_index([("title", ASCENDING)])
    movies_collection.create_index("genre")
    screenings_collection.create_index("movie_id")
    orders_collection.create_index("user_id")