from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .auth import hash_password
from .models import Movie, Showtime, User


def seed_data(db: Session) -> None:
    if not db.query(User).filter(User.username == "admin").first():
        db.add(User(username="admin", email="admin@cinema.local", password_hash=hash_password("admin123"), role="admin"))

    if not db.query(User).filter(User.username == "user").first():
        db.add(User(username="user", email="user@cinema.local", password_hash=hash_password("user123"), role="user"))

    db.commit()

    if db.query(Movie).count() == 0:
        movies = [
            Movie(title="Interstellar", genre="Sci-Fi", duration_minutes=169, description="Подорож крізь космос і час у пошуках нового дому для людства.", age_limit=12),
            Movie(title="Inception", genre="Thriller", duration_minutes=148, description="Історія про проникнення у сни та викрадення ідей.", age_limit=12),
            Movie(title="The Dark Knight", genre="Action", duration_minutes=152, description="Бетмен протистоїть Джокеру в небезпечній грі за Готем.", age_limit=16),
        ]
        db.add_all(movies)
        db.commit()

    if db.query(Showtime).count() == 0:
        movies = db.query(Movie).all()
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        showtimes = []
        for index, movie in enumerate(movies, start=1):
            showtimes.extend([
                Showtime(movie_id=movie.id, hall_name=f"Зал {index}", start_time=now + timedelta(hours=index * 2), total_seats=50, available_seats=50),
                Showtime(movie_id=movie.id, hall_name=f"VIP {index}", start_time=now + timedelta(days=1, hours=index * 3), total_seats=30, available_seats=30),
            ])
        db.add_all(showtimes)
        db.commit()
