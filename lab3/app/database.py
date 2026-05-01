import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, MongoClient, TEXT
from pymongo.database import Database

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "cinema_ticket_lab3")

client = MongoClient(MONGO_URI)
db: Database = client[MONGO_DB_NAME]


def get_db() -> Database:
    return db


def object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise ValueError("Invalid ObjectId")
    return ObjectId(value)


def serialize_doc(doc: Any) -> Any:
    """Convert ObjectId and datetime values to JSON-friendly strings."""
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        result: Dict[str, Any] = {}
        for key, value in doc.items():
            if key == "_id":
                result["id"] = str(value)
            elif isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.strftime("%Y-%m-%d %H:%M")
            else:
                result[key] = serialize_doc(value)
        return result
    return doc


def ensure_indexes() -> None:
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.users.create_index([("role", ASCENDING)])
    db.movies.create_index([("title", TEXT), ("genre", TEXT), ("description", TEXT)])
    db.movies.create_index([("created_at", DESCENDING)])
    db.screenings.create_index([("movie_id", ASCENDING), ("starts_at", ASCENDING)])
    db.ticket_orders.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    db.ticket_orders.create_index([("movie_id", ASCENDING)])


def seed_data(hash_password_func) -> None:
    """Create default administrator and demo data if collections are empty."""
    if db.users.count_documents({}) == 0:
        db.users.insert_many([
            {
                "email": "admin@cinema.local",
                "full_name": "Адміністратор кінотеатру",
                "password_hash": hash_password_func("admin123"),
                "role": "admin",
                "created_at": datetime.utcnow(),
            },
            {
                "email": "user@cinema.local",
                "full_name": "Тестовий користувач",
                "password_hash": hash_password_func("user123"),
                "role": "user",
                "created_at": datetime.utcnow(),
            },
        ])

    if db.movies.count_documents({}) == 0:
        movies: List[Dict[str, Any]] = [
            {
                "title": "Дюна: Частина друга",
                "genre": "Фантастика",
                "duration_minutes": 166,
                "age_limit": "12+",
                "description": "Епічна історія про боротьбу за майбутнє планети Арракіс.",
                "poster_url": "https://placehold.co/600x850?text=Dune+2",
                "created_at": datetime.utcnow(),
            },
            {
                "title": "Думками навиворіт 2",
                "genre": "Анімація",
                "duration_minutes": 96,
                "age_limit": "0+",
                "description": "Яскрава сімейна анімація про емоції, дорослішання та нові переживання.",
                "poster_url": "https://placehold.co/600x850?text=Inside+Out+2",
                "created_at": datetime.utcnow(),
            },
            {
                "title": "Каскадер",
                "genre": "Екшн",
                "duration_minutes": 126,
                "age_limit": "16+",
                "description": "Динамічна історія про каскадера, який опиняється у центрі небезпечної пригоди.",
                "poster_url": "https://placehold.co/600x850?text=Action",
                "created_at": datetime.utcnow(),
            },
        ]
        inserted = db.movies.insert_many(movies)
        now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        screenings: List[Dict[str, Any]] = []
        for index, movie_id in enumerate(inserted.inserted_ids):
            screenings.extend([
                {
                    "movie_id": movie_id,
                    "starts_at": now + timedelta(days=1, hours=2 + index),
                    "hall": f"Зал {index + 1}",
                    "price": 180 + index * 20,
                    "available_seats": 60,
                    "created_at": datetime.utcnow(),
                },
                {
                    "movie_id": movie_id,
                    "starts_at": now + timedelta(days=2, hours=5 + index),
                    "hall": f"Зал {index + 1}",
                    "price": 220 + index * 20,
                    "available_seats": 45,
                    "created_at": datetime.utcnow(),
                },
            ])
        db.screenings.insert_many(screenings)
