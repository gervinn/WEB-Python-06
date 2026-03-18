from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from starlette.middleware.sessions import SessionMiddleware

from .auth import (
    authenticate_user,
    get_current_user_from_session,
    hash_password,
    login_user,
    logout_user,
    require_admin,
    require_login,
)
from .database import Base, engine, get_db
from .models import Booking, Movie, Showtime, User
from .schemas import (
    BookingCreate,
    BookingOut,
    MovieCreate,
    MovieOut,
    MovieUpdate,
    ShowtimeCreate,
    ShowtimeOut,
    UserCreate,
    UserOut,
)
from .seed import seed_data

app = FastAPI(
    title="Cinema Tickets API",
    summary="Система замовлення квитків у кінотеатр",
    description="Навчальний RESTful API вебзастосунок із серверною генерацією HTML, ролями користувачів та SQLite базою даних.",
    version="1.0.0",
    docs_url="/documentation",
    redoc_url="/reference",
    openapi_url="/api/openapi.json",
    swagger_ui_parameters={"displayRequestDuration": True, "docExpansion": "list"},
    openapi_tags=[
        {"name": "Authentication", "description": "Реєстрація та вхід користувачів"},
        {"name": "Movies", "description": "CRUD-операції для фільмів"},
        {"name": "Showtimes", "description": "Керування сеансами"},
        {"name": "Bookings", "description": "Робота з бронюваннями"},
    ],
)

APP_DIR = Path(__file__).resolve().parent

app.add_middleware(SessionMiddleware, secret_key="super-secret-session-key")
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        seed_data(db)
    finally:
        db.close()


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Cinema Booking REST API",
        version="1.0.0",
        summary="Курсовий/лабораторний проєкт з теми замовлення квитків у кінотеатр",
        description=(
            "API та серверний HTML-застосунок для керування фільмами, сеансами та бронюваннями. "
            "Реалізовано ролі адміністратора і користувача, SQLAlchemy ORM та SQLite."
        ),
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


def render(request: Request, template_name: str, db: Session, context: Optional[dict] = None):
    user = get_current_user_from_session(request, db)
    base_context = {"request": request, "current_user": user, "error": None}
    if context:
        base_context.update(context)
    return templates.TemplateResponse(template_name, base_context)


def redirect_with_message(url: str, message: str, error: bool = False) -> RedirectResponse:
    query = f"?message={message}" if not error else f"?error={message}"
    return RedirectResponse(url=f"{url}{query}", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    movies = db.query(Movie).options(joinedload(Movie.showtimes)).all()
    return render(request, "home.html", db, {"movies": movies})


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    return render(request, "register.html", db)


@app.post("/register")
def register(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    try:
        payload = UserCreate(username=username, email=email, password=password)
    except ValidationError as exc:
        return render(request, "register.html", db, {"error": exc.errors()[0]["msg"]})

    if db.query(User).filter(or_(User.username == payload.username, User.email == payload.email)).first():
        return render(request, "register.html", db, {"error": "Користувач з таким логіном або email уже існує"})

    user = User(username=payload.username, email=payload.email, password_hash=hash_password(payload.password), role="user")
    db.add(user)
    db.commit()
    return redirect_with_message("/login", "Реєстрація успішна. Увійдіть у систему")


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    return render(request, "login.html", db)


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = authenticate_user(db, username, password)
    if not user:
        return render(request, "login.html", db, {"error": "Невірний логін або пароль"})
    login_user(request, user)
    return redirect_with_message("/", f"Вітаємо, {user.username}")


@app.post("/logout")
def logout(request: Request):
    logout_user(request)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/movies", response_class=HTMLResponse)
def movies_page(request: Request, db: Session = Depends(get_db)):
    movies = db.query(Movie).order_by(Movie.title).all()
    return render(request, "movies.html", db, {"movies": movies})


@app.get("/movies/new", response_class=HTMLResponse)
def create_movie_page(request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    return render(request, "movie_form.html", db, {"page_title": "Додати фільм", "movie": None})


@app.post("/movies/new")
def create_movie_html(request: Request, title: str = Form(...), genre: str = Form(...), duration_minutes: int = Form(...), description: str = Form(...), age_limit: int = Form(...), db: Session = Depends(get_db)):
    require_admin(request, db)
    try:
        payload = MovieCreate(title=title, genre=genre, duration_minutes=duration_minutes, description=description, age_limit=age_limit)
    except ValidationError as exc:
        return render(request, "movie_form.html", db, {"page_title": "Додати фільм", "movie": None, "error": exc.errors()[0]["msg"]})
    movie = Movie(**payload.model_dump())
    db.add(movie)
    db.commit()
    return redirect_with_message("/movies", "Фільм успішно додано")


@app.get("/movies/{movie_id}/edit", response_class=HTMLResponse)
def edit_movie_page(movie_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Фільм не знайдено")
    return render(request, "movie_form.html", db, {"page_title": "Редагувати фільм", "movie": movie})


@app.post("/movies/{movie_id}/edit")
def edit_movie_html(movie_id: int, request: Request, title: str = Form(...), genre: str = Form(...), duration_minutes: int = Form(...), description: str = Form(...), age_limit: int = Form(...), db: Session = Depends(get_db)):
    require_admin(request, db)
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Фільм не знайдено")
    try:
        payload = MovieUpdate(title=title, genre=genre, duration_minutes=duration_minutes, description=description, age_limit=age_limit)
    except ValidationError as exc:
        return render(request, "movie_form.html", db, {"page_title": "Редагувати фільм", "movie": movie, "error": exc.errors()[0]["msg"]})
    for key, value in payload.model_dump().items():
        setattr(movie, key, value)
    db.commit()
    return redirect_with_message("/movies", "Фільм успішно оновлено")


@app.post("/movies/{movie_id}/delete")
def delete_movie_html(movie_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Фільм не знайдено")
    db.delete(movie)
    db.commit()
    return redirect_with_message("/movies", "Фільм успішно видалено")


@app.get("/showtimes", response_class=HTMLResponse)
def showtimes_page(request: Request, db: Session = Depends(get_db)):
    showtimes = db.query(Showtime).options(joinedload(Showtime.movie)).order_by(Showtime.start_time).all()
    movies = db.query(Movie).order_by(Movie.title).all()
    return render(request, "showtimes.html", db, {"showtimes": showtimes, "movies": movies})


@app.post("/showtimes/new")
def create_showtime_html(request: Request, movie_id: int = Form(...), hall_name: str = Form(...), start_time: str = Form(...), total_seats: int = Form(...), db: Session = Depends(get_db)):
    require_admin(request, db)
    try:
        payload = ShowtimeCreate(movie_id=movie_id, hall_name=hall_name, start_time=datetime.fromisoformat(start_time), total_seats=total_seats)
    except (ValidationError, ValueError):
        return redirect_with_message("/showtimes", "Некоректні дані сеансу", error=True)
    movie = db.query(Movie).filter(Movie.id == payload.movie_id).first()
    if not movie:
        return redirect_with_message("/showtimes", "Фільм не знайдено", error=True)
    showtime = Showtime(movie_id=payload.movie_id, hall_name=payload.hall_name, start_time=payload.start_time, total_seats=payload.total_seats, available_seats=payload.total_seats)
    db.add(showtime)
    db.commit()
    return redirect_with_message("/showtimes", "Сеанс успішно додано")


@app.post("/bookings/create")
def create_booking_html(request: Request, showtime_id: int = Form(...), seats_reserved: int = Form(...), db: Session = Depends(get_db)):
    user = require_login(request, db)
    showtime = db.query(Showtime).filter(Showtime.id == showtime_id).first()
    if not showtime:
        return redirect_with_message("/showtimes", "Сеанс не знайдено", error=True)
    if seats_reserved <= 0:
        return redirect_with_message("/showtimes", "Кількість місць має бути більшою за нуль", error=True)
    if showtime.available_seats < seats_reserved:
        return redirect_with_message("/showtimes", "Недостатньо вільних місць", error=True)
    booking = Booking(user_id=user.id, showtime_id=showtime.id, seats_reserved=seats_reserved)
    showtime.available_seats -= seats_reserved
    db.add(booking)
    db.commit()
    return redirect_with_message("/my-bookings", "Бронювання успішно створено")


@app.get("/my-bookings", response_class=HTMLResponse)
def my_bookings_page(request: Request, db: Session = Depends(get_db)):
    user = require_login(request, db)
    bookings = db.query(Booking).options(joinedload(Booking.showtime).joinedload(Showtime.movie)).filter(Booking.user_id == user.id).order_by(Booking.booked_at.desc()).all()
    return render(request, "my_bookings.html", db, {"bookings": bookings})


@app.get("/admin/bookings", response_class=HTMLResponse)
def admin_bookings_page(request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    bookings = db.query(Booking).options(joinedload(Booking.user), joinedload(Booking.showtime).joinedload(Showtime.movie)).order_by(Booking.booked_at.desc()).all()
    return render(request, "admin_bookings.html", db, {"bookings": bookings})


@app.get("/api/profile", response_model=UserOut, tags=["Authentication"])
def api_profile(request: Request, db: Session = Depends(get_db)):
    user = require_login(request, db)
    return user


@app.get("/api/movies", response_model=list[MovieOut], tags=["Movies"])
def api_list_movies(db: Session = Depends(get_db)):
    return db.query(Movie).order_by(Movie.id).all()


@app.get("/api/movies/{movie_id}", response_model=MovieOut, tags=["Movies"])
def api_get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Фільм не знайдено")
    return movie


@app.post("/api/movies", response_model=MovieOut, status_code=201, tags=["Movies"])
def api_create_movie(request: Request, payload: MovieCreate, db: Session = Depends(get_db)):
    require_admin(request, db)
    movie = Movie(**payload.model_dump())
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return movie


@app.put("/api/movies/{movie_id}", response_model=MovieOut, tags=["Movies"])
def api_update_movie(movie_id: int, request: Request, payload: MovieUpdate, db: Session = Depends(get_db)):
    require_admin(request, db)
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Фільм не знайдено")
    for key, value in payload.model_dump().items():
        setattr(movie, key, value)
    db.commit()
    db.refresh(movie)
    return movie


@app.delete("/api/movies/{movie_id}", tags=["Movies"])
def api_delete_movie(movie_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Фільм не знайдено")
    db.delete(movie)
    db.commit()
    return JSONResponse({"message": "Фільм видалено"})


@app.get("/api/showtimes", response_model=list[ShowtimeOut], tags=["Showtimes"])
def api_list_showtimes(db: Session = Depends(get_db)):
    return db.query(Showtime).order_by(Showtime.start_time).all()


@app.post("/api/showtimes", response_model=ShowtimeOut, status_code=201, tags=["Showtimes"])
def api_create_showtime(request: Request, payload: ShowtimeCreate, db: Session = Depends(get_db)):
    require_admin(request, db)
    movie = db.query(Movie).filter(Movie.id == payload.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Фільм не знайдено")
    showtime = Showtime(movie_id=payload.movie_id, hall_name=payload.hall_name, start_time=payload.start_time, total_seats=payload.total_seats, available_seats=payload.total_seats)
    db.add(showtime)
    db.commit()
    db.refresh(showtime)
    return showtime


@app.post("/api/bookings", response_model=BookingOut, status_code=201, tags=["Bookings"])
def api_create_booking(request: Request, payload: BookingCreate, db: Session = Depends(get_db)):
    user = require_login(request, db)
    showtime = db.query(Showtime).filter(Showtime.id == payload.showtime_id).first()
    if not showtime:
        raise HTTPException(status_code=404, detail="Сеанс не знайдено")
    if showtime.available_seats < payload.seats_reserved:
        raise HTTPException(status_code=400, detail="Недостатньо вільних місць")
    booking = Booking(user_id=user.id, showtime_id=showtime.id, seats_reserved=payload.seats_reserved)
    showtime.available_seats -= payload.seats_reserved
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@app.get("/api/bookings/my", response_model=list[BookingOut], tags=["Bookings"])
def api_my_bookings(request: Request, db: Session = Depends(get_db)):
    user = require_login(request, db)
    return db.query(Booking).filter(Booking.user_id == user.id).order_by(Booking.booked_at.desc()).all()
