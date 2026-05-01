from typing import Optional

from pydantic import BaseModel, Field


class MovieCreate(BaseModel):
    title: str = Field(..., min_length=2, examples=["Avatar"])
    genre: str = Field(..., min_length=2, examples=["Fantasy"])
    duration_minutes: int = Field(..., ge=1, le=400, examples=[160])
    age_limit: str = Field(default="0+", examples=["12+"])
    description: str = Field(default="", examples=["Опис фільму"])
    poster_url: str = Field(default="", examples=["https://placehold.co/600x850"])


class MovieUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2)
    genre: Optional[str] = Field(default=None, min_length=2)
    duration_minutes: Optional[int] = Field(default=None, ge=1, le=400)
    age_limit: Optional[str] = None
    description: Optional[str] = None
    poster_url: Optional[str] = None


class OrderCreate(BaseModel):
    screening_id: str
    seats_count: int = Field(..., ge=1, le=10)
