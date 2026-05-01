from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MovieCreate(BaseModel):
    title: str = Field(..., min_length=2, examples=["Дюна: Частина друга"])
    genre: str = Field(..., examples=["Фантастика"])
    duration_minutes: int = Field(..., ge=1, examples=[166])
    age_rating: str = Field("12+", examples=["12+"])
    description: str = Field(..., min_length=5, examples=["Фантастичний фільм про боротьбу за майбутнє."])
    poster_url: Optional[str] = Field(None, examples=["https://example.com/poster.jpg"])


class MovieUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2)
    genre: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=1)
    age_rating: Optional[str] = None
    description: Optional[str] = Field(None, min_length=5)
    poster_url: Optional[str] = None


class MovieRead(BaseModel):
    id: int
    title: str
    genre: str
    duration_minutes: int
    age_rating: str
    description: str
    poster_url: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ScreeningRead(BaseModel):
    id: int
    movie_id: int
    hall: str
    starts_at: datetime
    price: float
    available_seats: int

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    screening_id: int
    seats_count: int = Field(..., ge=1, le=10)


class OrderRead(BaseModel):
    id: int
    screening_id: int
    seats_count: int
    total_price: float
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
