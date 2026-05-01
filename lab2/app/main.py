from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from starlette.middleware.sessions import SessionMiddleware

from .auth import (
    get_current_user_basic,
    get_current_user_from_session,
    get_user_by_email,
    hash_password,
    require_admin,
    require_admin_basic,
    require_login,
    verify_password,
)
from .database import Base, SessionLocal, engine, get_db
from .models import Movie, Screening, TicketOrder, User
from .schemas import MovieCreate, MovieRead, MovieUpdate, OrderCreate, OrderRead, ScreeningRead

app = FastAPI(
    title="Cinema Ticket Ordering API",
    description="RESTful API вебзастосунок для замовлення квитків у кінотеатр. HTML генерується на сервері, дані зберігаються в PostgreSQL через SQLAlchemy ORM.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "HTML pages", "description": "Сторінки, що генеруються на сервері та відправляються клієнту у вигляді HTML."},
        {"name": "Movies API", "description": "RESTful CRUD-операції для сутності Movie."},
        {"name": "Screenings API", "description": "API для перегляду кіносеансів."},
        {"name": "Orders API", "description": "API для створення та перегляду замовлень квитків."},
    ],
)

app.add_middleware(SessionMiddleware, secret_key="change-this-secret-key-for-production")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Cinema Ticket Ordering API — навчальний проєкт",
        version="1.0.0",
        description=(
            "Кастомізована OpenAPI документація для предметної галузі "
            "'Замовлення квитків у кінотеатр'. Для адміністративних API-запитів "
            "використовується HTTP Basic Auth."
        ),
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    openapi_schema["servers"] = [{"url": "http://127.0.0.1:8000", "description": "Local development server"}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = get_user_by_email(db, "admin@cinema.local")
        if not admin:
            admin = User(
                email="admin@cinema.local",
                full_name="Адміністратор кінотеатру",
                password_hash=hash_password("admin123"),
                role="admin",
            )
            db.add(admin)
            db.commit()

        movies_count = db.query(Movie).count()
        if movies_count == 0:
            movie_1 = Movie(
                title="Дюна: Частина друга",
                genre="Фантастика",
                duration_minutes=166,
                age_rating="12+",
                description="Епічна історія про боротьбу за владу, ресурси та майбутнє планети Арракіс.",
                poster_url="https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=800&q=80",
            )
            movie_2 = Movie(
                title="Думками навиворіт 2",
                genre="Анімація",
                duration_minutes=96,
                age_rating="0+",
                description="Сімейна анімаційна історія про емоції, дорослішання та прийняття себе.",
                poster_url="https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=800&q=80",
            )
            movie_3 = Movie(
                title="Оппенгеймер",
                genre="Драма",
                duration_minutes=180,
                age_rating="16+",
                description="Біографічна драма про науковця, рішення якого вплинули на історію людства.",
                poster_url="https://images.unsplash.com/photo-1440404653325-ab127d49abc1?auto=format&fit=crop&w=800&q=80",
            )
            db.add_all([movie_1, movie_2, movie_3])
            db.commit()
            db.refresh(movie_1)
            db.refresh(movie_2)
            db.refresh(movie_3)

            now = datetime.now().replace(second=0, microsecond=0)
            screenings = [
                Screening(movie_id=movie_1.id, hall="Зал 1", starts_at=now + timedelta(days=1, hours=2), price=220.0, available_seats=60),
                Screening(movie_id=movie_1.id, hall="Зал 2", starts_at=now + timedelta(days=2, hours=4), price=250.0, available_seats=48),
                Screening(movie_id=movie_2.id, hall="Зал 3", starts_at=now + timedelta(days=1, hours=5), price=180.0, available_seats=80),
                Screening(movie_id=movie_3.id, hall="Зал 1", starts_at=now + timedelta(days=3, hours=1), price=210.0, available_seats=55),
            ]
            db.add_all(screenings)
            db.commit()
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    init_db()


def render(request: Request, template: str, context: Optional[dict] = None):
    context = context or {}
    return templates.TemplateResponse(
        template,
        {
            "request": request,
            "current_user": context.pop("current_user", None),
            **context,
        },
    )


@app.get("/", response_class=HTMLResponse, tags=["HTML pages"])
def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_session(request, db)
    movies = db.query(Movie).options(joinedload(Movie.screenings)).order_by(Movie.created_at.desc()).all()
    return render(request, "index.html", {"movies": movies, "current_user": user})


@app.get("/register", response_class=HTMLResponse, tags=["HTML pages"])
def register_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_session(request, db)
    return render(request, "register.html", {"current_user": user})


@app.post("/register", response_class=HTMLResponse, tags=["HTML pages"])
def register_action(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    normalized_email = email.lower().strip()
    if get_user_by_email(db, normalized_email):
        return render(request, "register.html", {"error": "Користувач з таким email вже існує."})
    if len(password) < 6:
        return render(request, "register.html", {"error": "Пароль має містити щонайменше 6 символів."})

    user = User(
        full_name=full_name.strip(),
        email=normalized_email,
        password_hash=hash_password(password),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/login", response_class=HTMLResponse, tags=["HTML pages"])
def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_session(request, db)
    return render(request, "login.html", {"current_user": user})


@app.post("/login", response_class=HTMLResponse, tags=["HTML pages"])
def login_action(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        return render(request, "login.html", {"error": "Неправильний email або пароль."})
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/logout", tags=["HTML pages"])
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/movies", response_class=HTMLResponse, tags=["HTML pages"])
def movies_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_session(request, db)
    movies = db.query(Movie).order_by(Movie.created_at.desc()).all()
    return render(request, "movies.html", {"movies": movies, "current_user": user})


@app.get("/movies/{movie_id}", response_class=HTMLResponse, tags=["HTML pages"])
def movie_detail_page(movie_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_session(request, db)
    movie = db.query(Movie).options(joinedload(Movie.screenings)).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Фільм не знайдено")
    return render(request, "movie_detail.html", {"movie": movie, "current_user": user})


@app.get("/book/{screening_id}", response_class=HTMLResponse, tags=["HTML pages"])
def booking_page(
    screening_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_login),
):
    screening = db.query(Screening).options(joinedload(Screening.movie)).filter(Screening.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=404, detail="Сеанс не знайдено")
    return render(request, "booking.html", {"screening": screening, "current_user": user})


@app.post("/book/{screening_id}", response_class=HTMLResponse, tags=["HTML pages"])
def booking_action(
    screening_id: int,
    request: Request,
    seats_count: int = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_login),
):
    screening = db.query(Screening).options(joinedload(Screening.movie)).filter(Screening.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=404, detail="Сеанс не знайдено")
    if seats_count < 1:
        return render(request, "booking.html", {"screening": screening, "current_user": user, "error": "Кількість місць має бути більшою за 0."})
    if seats_count > screening.available_seats:
        return render(request, "booking.html", {"screening": screening, "current_user": user, "error": "Недостатньо вільних місць."})

    order = TicketOrder(
        user_id=user.id,
        screening_id=screening.id,
        seats_count=seats_count,
        total_price=round(seats_count * screening.price, 2),
        status="created",
    )
    screening.available_seats -= seats_count
    db.add(order)
    db.commit()
    return RedirectResponse(url="/my-orders", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/my-orders", response_class=HTMLResponse, tags=["HTML pages"])
def my_orders_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_login),
):
    orders = (
        db.query(TicketOrder)
        .options(joinedload(TicketOrder.screening).joinedload(Screening.movie))
        .filter(TicketOrder.user_id == user.id)
        .order_by(TicketOrder.created_at.desc())
        .all()
    )
    return render(request, "my_orders.html", {"orders": orders, "current_user": user})


@app.get("/admin", response_class=HTMLResponse, tags=["HTML pages"])
def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    stats = {
        "users": db.query(User).count(),
        "movies": db.query(Movie).count(),
        "screenings": db.query(Screening).count(),
        "orders": db.query(TicketOrder).count(),
    }
    return render(request, "admin_dashboard.html", {"stats": stats, "current_user": user})


@app.get("/admin/movies", response_class=HTMLResponse, tags=["HTML pages"])
def admin_movies_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    movies = db.query(Movie).order_by(Movie.created_at.desc()).all()
    return render(request, "admin_movies.html", {"movies": movies, "current_user": user})


@app.get("/admin/movies/create", response_class=HTMLResponse, tags=["HTML pages"])
def admin_movie_create_page(
    request: Request,
    user: User = Depends(require_admin),
):
    return render(request, "movie_form.html", {"movie": None, "action": "/admin/movies/create", "current_user": user})


@app.post("/admin/movies/create", response_class=HTMLResponse, tags=["HTML pages"])
def admin_movie_create_action(
    request: Request,
    title: str = Form(...),
    genre: str = Form(...),
    duration_minutes: int = Form(...),
    age_rating: str = Form(...),
    description: str = Form(...),
    poster_url: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    movie = Movie(
        title=title.strip(),
        genre=genre.strip(),
        duration_minutes=duration_minutes,
        age_rating=age_rating.strip(),
        description=description.strip(),
        poster_url=poster_url.strip() or None,
    )
    db.add(movie)
    db.commit()
    return RedirectResponse(url="/admin/movies", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/admin/movies/{movie_id}/edit", response_class=HTMLResponse, tags=["HTML pages"])
def admin_movie_edit_page(
    movie_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Фільм не знайдено")
    return render(request, "movie_form.html", {"movie": movie, "action": f"/admin/movies/{movie.id}/edit", "current_user": user})


@app.post("/admin/movies/{movie_id}/edit", response_class=HTMLResponse, tags=["HTML pages"])
def admin_movie_edit_action(
    movie_id: int,
    title: str = Form(...),
    genre: str = Form(...),
    duration_minutes: int = Form(...),
    age_rating: str = Form(...),
    description: str = Form(...),
    poster_url: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Фільм не знайдено")
    movie.title = title.strip()
    movie.genre = genre.strip()
    movie.duration_minutes = duration_minutes
    movie.age_rating = age_rating.strip()
    movie.description = description.strip()
    movie.poster_url = poster_url.strip() or None
    db.commit()
    return RedirectResponse(url="/admin/movies", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/admin/movies/{movie_id}/delete", response_class=HTMLResponse, tags=["HTML pages"])
def admin_movie_delete_action(
    movie_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Фільм не знайдено")
    db.delete(movie)
    db.commit()
    return RedirectResponse(url="/admin/movies", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/api/movies", response_model=list[MovieRead], tags=["Movies API"])
def api_get_movies(db: Session = Depends(get_db)):
    return db.query(Movie).order_by(Movie.created_at.desc()).all()


@app.get("/api/movies/{movie_id}", response_model=MovieRead, tags=["Movies API"])
def api_get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Фільм не знайдено")
    return movie


@app.post("/api/movies", response_model=MovieRead, status_code=status.HTTP_201_CREATED, tags=["Movies API"])
def api_create_movie(
    payload: MovieCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_basic),
):
    movie = Movie(**payload.model_dump())
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return movie


@app.put("/api/movies/{movie_id}", response_model=MovieRead, tags=["Movies API"])
def api_update_movie(
    movie_id: int,
    payload: MovieUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_basic),
):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Фільм не знайдено")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(movie, key, value)
    db.commit()
    db.refresh(movie)
    return movie


@app.delete("/api/movies/{movie_id}", tags=["Movies API"])
def api_delete_movie(
    movie_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_basic),
):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Фільм не знайдено")
    db.delete(movie)
    db.commit()
    return {"message": "Фільм успішно видалено", "deleted_movie_id": movie_id}


@app.get("/api/screenings", response_model=list[ScreeningRead], tags=["Screenings API"])
def api_get_screenings(db: Session = Depends(get_db)):
    return db.query(Screening).order_by(Screening.starts_at.asc()).all()


@app.post("/api/orders", response_model=OrderRead, status_code=status.HTTP_201_CREATED, tags=["Orders API"])
def api_create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_basic),
):
    screening = db.query(Screening).filter(Screening.id == payload.screening_id).first()
    if not screening:
        raise HTTPException(status_code=404, detail="Сеанс не знайдено")
    if payload.seats_count > screening.available_seats:
        raise HTTPException(status_code=400, detail="Недостатньо вільних місць")

    order = TicketOrder(
        user_id=user.id,
        screening_id=screening.id,
        seats_count=payload.seats_count,
        total_price=round(payload.seats_count * screening.price, 2),
        status="created",
    )
    screening.available_seats -= payload.seats_count
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@app.get("/api/orders/me", response_model=list[OrderRead], tags=["Orders API"])
def api_get_my_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_basic),
):
    return (
        db.query(TicketOrder)
        .filter(TicketOrder.user_id == user.id)
        .order_by(TicketOrder.created_at.desc())
        .all()
    )
