from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, index=True, nullable=False)
    full_name = Column(String(120), nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(20), default="user", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    orders = relationship("TicketOrder", back_populates="user", cascade="all, delete-orphan")


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False, index=True)
    genre = Column(String(80), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    age_rating = Column(String(10), default="0+")
    description = Column(Text, nullable=False)
    poster_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    screenings = relationship("Screening", back_populates="movie", cascade="all, delete-orphan")


class Screening(Base):
    __tablename__ = "screenings"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    hall = Column(String(50), nullable=False)
    starts_at = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)
    available_seats = Column(Integer, nullable=False)

    movie = relationship("Movie", back_populates="screenings")
    orders = relationship("TicketOrder", back_populates="screening", cascade="all, delete-orphan")


class TicketOrder(Base):
    __tablename__ = "ticket_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    screening_id = Column(Integer, ForeignKey("screenings.id", ondelete="CASCADE"), nullable=False)
    seats_count = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String(30), default="created", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="orders")
    screening = relationship("Screening", back_populates="orders")
