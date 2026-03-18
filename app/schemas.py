from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=4, max_length=100)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    role: str


class MovieBase(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    genre: str = Field(min_length=1, max_length=80)
    duration_minutes: int = Field(gt=0)
    description: str = Field(min_length=5)
    age_limit: int = Field(ge=0, le=21)


class MovieCreate(MovieBase):
    pass


class MovieUpdate(MovieBase):
    pass


class MovieOut(MovieBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class ShowtimeCreate(BaseModel):
    movie_id: int
    hall_name: str = Field(min_length=1, max_length=50)
    start_time: datetime
    total_seats: int = Field(gt=0)


class ShowtimeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movie_id: int
    hall_name: str
    start_time: datetime
    total_seats: int
    available_seats: int


class BookingCreate(BaseModel):
    showtime_id: int
    seats_reserved: int = Field(gt=0)


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    showtime_id: int
    seats_reserved: int
    booked_at: datetime
