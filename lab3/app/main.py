from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from .auth import get_current_user, hash_password, require_api_admin, require_api_user, verify_password
from .database import db, ensure_indexes, object_id, seed_data, serialize_doc
from .schemas import MovieCreate, MovieUpdate, OrderCreate

app = FastAPI(
    title="Cinema Ticket MongoDB API",
    description=(
        "Лабораторна робота №3: міграція вебзастосунку замовлення квитків "
        "у кінотеатр з реляційної БД SQLite на MongoDB із використанням pymongo."
    ),
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "HTML", "description": "Серверна генерація HTML-сторінок Jinja2."},
        {"name": "Auth", "description": "Реєстрація, авторизація та ролі користувачів."},
        {"name": "Movies", "description": "CRUD-операції для сутності Movie у MongoDB."},
        {"name": "Orders", "description": "Замовлення квитків користувачами."},
        {"name": "MongoDB", "description": "Текстовий пошук та aggregation pipeline."},
    ],
)

app.add_middleware(
    __import__("starlette.middleware.sessions", fromlist=["SessionMiddleware"]).SessionMiddleware,
    secret_key="cinema-lab3-secret-key-change-in-production",
    same_site="lax",
    https_only=False,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://placehold.co/160x80?text=Cinema+MongoDB"
    }
    openapi_schema["info"]["contact"] = {
        "name": "Навчальний RESTful API проєкт",
        "email": "admin@cinema.local",
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.on_event("startup")
def startup_event() -> None:
    ensure_indexes()
    seed_data(hash_password)


def page_context(request: Request, **kwargs):
    return {
        "request": request,
        "current_user": serialize_doc(get_current_user(request, db)),
        **kwargs,
    }


def redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


def get_movie_or_404(movie_id: str) -> dict:
    try:
        oid = object_id(movie_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Фільм не знайдено")
    movie = db.movies.find_one({"_id": oid})
    if not movie:
        raise HTTPException(status_code=404, detail="Фільм не знайдено")
    return movie


def get_screening_or_404(screening_id: str) -> dict:
    try:
        oid = object_id(screening_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Сеанс не знайдено")
    screening = db.screenings.find_one({"_id": oid})
    if not screening:
        raise HTTPException(status_code=404, detail="Сеанс не знайдено")
    return screening


def current_user_or_redirect(request: Request) -> Optional[dict]:
    return get_current_user(request, db)


def admin_or_redirect(request: Request) -> Optional[dict]:
    user = get_current_user(request, db)
    if not user or user.get("role") != "admin":
        return None
    return user


def movie_payload_from_form(
    title: str,
    genre: str,
    duration_minutes: int,
    age_limit: str,
    description: str,
    poster_url: str,
) -> dict:
    return {
        "title": title.strip(),
        "genre": genre.strip(),
        "duration_minutes": int(duration_minutes),
        "age_limit": age_limit.strip() or "0+",
        "description": description.strip(),
        "poster_url": poster_url.strip() or "https://placehold.co/600x850?text=Cinema",
    }


# ------------------------- HTML ROUTES -------------------------


@app.get("/", response_class=HTMLResponse, tags=["HTML"])
def home(request: Request):
    movies = list(db.movies.find().sort("created_at", -1).limit(6))
    stats = list(
        db.ticket_orders.aggregate(
            [
                {
                    "$group": {
                        "_id": "$movie_id",
                        "movie_title": {"$first": "$movie_title"},
                        "tickets": {"$sum": "$seats_count"},
                        "revenue": {"$sum": "$total_price"},
                    }
                },
                {"$sort": {"tickets": -1}},
                {"$limit": 3},
            ]
        )
    )
    return templates.TemplateResponse(
        "index.html",
        page_context(request, movies=serialize_doc(movies), stats=serialize_doc(stats)),
    )


@app.get("/register", response_class=HTMLResponse, tags=["Auth"])
def register_page(request: Request):
    return templates.TemplateResponse("register.html", page_context(request))


@app.post("/register", response_class=HTMLResponse, tags=["Auth"])
def register(
    request: Request,
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
):
    try:
        result = db.users.insert_one(
            {
                "email": email.lower().strip(),
                "full_name": full_name.strip(),
                "password_hash": hash_password(password),
                "role": "user",
                "created_at": datetime.utcnow(),
            }
        )
    except DuplicateKeyError:
        return templates.TemplateResponse(
            "register.html",
            page_context(request, error="Користувач із таким email вже існує."),
            status_code=400,
        )
    request.session["user_id"] = str(result.inserted_id)
    return redirect("/movies")


@app.get("/login", response_class=HTMLResponse, tags=["Auth"])
def login_page(request: Request):
    return templates.TemplateResponse("login.html", page_context(request))


@app.post("/login", response_class=HTMLResponse, tags=["Auth"])
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = db.users.find_one({"email": email.lower().strip()})
    if not user or not verify_password(password, user.get("password_hash", "")):
        return templates.TemplateResponse(
            "login.html",
            page_context(request, error="Неправильний email або пароль."),
            status_code=400,
        )
    request.session["user_id"] = str(user["_id"])
    return redirect("/admin" if user.get("role") == "admin" else "/movies")


@app.get("/logout", tags=["Auth"])
def logout(request: Request):
    request.session.clear()
    return redirect("/")


@app.get("/movies", response_class=HTMLResponse, tags=["HTML"])
def movies_page(request: Request, search: str = ""):
    query = {}
    if search.strip():
        query = {"$text": {"$search": search.strip()}}
        movies = list(db.movies.find(query, {"score": {"$meta": "textScore"}}).sort([("score", {"$meta": "textScore"})]))
    else:
        movies = list(db.movies.find().sort("created_at", -1))
    return templates.TemplateResponse(
        "movies.html",
        page_context(request, movies=serialize_doc(movies), search=search),
    )


@app.get("/movies/{movie_id}", response_class=HTMLResponse, tags=["HTML"])
def movie_detail(request: Request, movie_id: str):
    movie = get_movie_or_404(movie_id)
    screenings = list(db.screenings.find({"movie_id": movie["_id"]}).sort("starts_at", 1))
    return templates.TemplateResponse(
        "movie_detail.html",
        page_context(request, movie=serialize_doc(movie), screenings=serialize_doc(screenings)),
    )


@app.get("/booking/{screening_id}", response_class=HTMLResponse, tags=["Orders"])
def booking_page(request: Request, screening_id: str):
    user = current_user_or_redirect(request)
    if not user:
        return redirect("/login")
    screening = get_screening_or_404(screening_id)
    movie = db.movies.find_one({"_id": screening["movie_id"]})
    return templates.TemplateResponse(
        "booking.html",
        page_context(request, movie=serialize_doc(movie), screening=serialize_doc(screening)),
    )


@app.post("/booking/{screening_id}", response_class=HTMLResponse, tags=["Orders"])
def create_booking(request: Request, screening_id: str, seats_count: int = Form(...)):
    user = current_user_or_redirect(request)
    if not user:
        return redirect("/login")
    screening = get_screening_or_404(screening_id)
    seats_count = max(1, min(int(seats_count), 10))

    updated_screening = db.screenings.find_one_and_update(
        {"_id": screening["_id"], "available_seats": {"$gte": seats_count}},
        {"$inc": {"available_seats": -seats_count}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated_screening:
        movie = db.movies.find_one({"_id": screening["movie_id"]})
        return templates.TemplateResponse(
            "booking.html",
            page_context(
                request,
                movie=serialize_doc(movie),
                screening=serialize_doc(screening),
                error="Недостатньо доступних місць для замовлення.",
            ),
            status_code=400,
        )

    movie = db.movies.find_one({"_id": screening["movie_id"]})
    db.ticket_orders.insert_one(
        {
            "user_id": user["_id"],
            "user_email": user["email"],
            "movie_id": movie["_id"],
            "screening_id": updated_screening["_id"],
            "movie_title": movie["title"],
            "screening": {
                "starts_at": updated_screening["starts_at"],
                "hall": updated_screening["hall"],
                "price": updated_screening["price"],
            },
            "seats_count": seats_count,
            "total_price": seats_count * int(updated_screening["price"]),
            "status": "confirmed",
            "created_at": datetime.utcnow(),
        }
    )
    return redirect("/my-orders")


@app.get("/my-orders", response_class=HTMLResponse, tags=["Orders"])
def my_orders(request: Request):
    user = current_user_or_redirect(request)
    if not user:
        return redirect("/login")
    orders = list(db.ticket_orders.find({"user_id": user["_id"]}).sort("created_at", -1))
    return templates.TemplateResponse(
        "my_orders.html",
        page_context(request, orders=serialize_doc(orders)),
    )


@app.get("/admin", response_class=HTMLResponse, tags=["HTML"])
def admin_dashboard(request: Request):
    user = admin_or_redirect(request)
    if not user:
        return redirect("/login")
    counters = {
        "users": db.users.count_documents({}),
        "movies": db.movies.count_documents({}),
        "screenings": db.screenings.count_documents({}),
        "orders": db.ticket_orders.count_documents({}),
    }
    stats = list(
        db.ticket_orders.aggregate(
            [
                {
                    "$group": {
                        "_id": "$movie_id",
                        "movie_title": {"$first": "$movie_title"},
                        "orders_count": {"$sum": 1},
                        "tickets": {"$sum": "$seats_count"},
                        "revenue": {"$sum": "$total_price"},
                    }
                },
                {"$sort": {"revenue": -1}},
            ]
        )
    )
    return templates.TemplateResponse(
        "admin_dashboard.html",
        page_context(request, counters=counters, stats=serialize_doc(stats)),
    )


@app.get("/admin/movies", response_class=HTMLResponse, tags=["Movies"])
def admin_movies(request: Request):
    user = admin_or_redirect(request)
    if not user:
        return redirect("/login")
    movies = list(db.movies.find().sort("created_at", -1))
    return templates.TemplateResponse(
        "admin_movies.html",
        page_context(request, movies=serialize_doc(movies)),
    )


@app.get("/admin/movies/create", response_class=HTMLResponse, tags=["Movies"])
def admin_movie_create_page(request: Request):
    user = admin_or_redirect(request)
    if not user:
        return redirect("/login")
    return templates.TemplateResponse(
        "movie_form.html",
        page_context(request, action="create", movie={}),
    )


@app.post("/admin/movies/create", response_class=HTMLResponse, tags=["Movies"])
def admin_movie_create(
    request: Request,
    title: str = Form(...),
    genre: str = Form(...),
    duration_minutes: int = Form(...),
    age_limit: str = Form("0+"),
    description: str = Form(""),
    poster_url: str = Form(""),
):
    user = admin_or_redirect(request)
    if not user:
        return redirect("/login")
    payload = movie_payload_from_form(title, genre, duration_minutes, age_limit, description, poster_url)
    payload["created_at"] = datetime.utcnow()
    movie_id = db.movies.insert_one(payload).inserted_id
    db.screenings.insert_one(
        {
            "movie_id": movie_id,
            "starts_at": datetime.utcnow().replace(minute=0, second=0, microsecond=0),
            "hall": "Зал 1",
            "price": 180,
            "available_seats": 50,
            "created_at": datetime.utcnow(),
        }
    )
    return redirect("/admin/movies")


@app.get("/admin/movies/{movie_id}/edit", response_class=HTMLResponse, tags=["Movies"])
def admin_movie_edit_page(request: Request, movie_id: str):
    user = admin_or_redirect(request)
    if not user:
        return redirect("/login")
    movie = get_movie_or_404(movie_id)
    return templates.TemplateResponse(
        "movie_form.html",
        page_context(request, action="edit", movie=serialize_doc(movie)),
    )


@app.post("/admin/movies/{movie_id}/edit", response_class=HTMLResponse, tags=["Movies"])
def admin_movie_edit(
    request: Request,
    movie_id: str,
    title: str = Form(...),
    genre: str = Form(...),
    duration_minutes: int = Form(...),
    age_limit: str = Form("0+"),
    description: str = Form(""),
    poster_url: str = Form(""),
):
    user = admin_or_redirect(request)
    if not user:
        return redirect("/login")
    movie = get_movie_or_404(movie_id)
    payload = movie_payload_from_form(title, genre, duration_minutes, age_limit, description, poster_url)
    payload["updated_at"] = datetime.utcnow()
    db.movies.update_one({"_id": movie["_id"]}, {"$set": payload})
    return redirect("/admin/movies")


@app.post("/admin/movies/{movie_id}/delete", response_class=HTMLResponse, tags=["Movies"])
def admin_movie_delete(request: Request, movie_id: str):
    user = admin_or_redirect(request)
    if not user:
        return redirect("/login")
    movie = get_movie_or_404(movie_id)
    db.screenings.delete_many({"movie_id": movie["_id"]})
    db.ticket_orders.delete_many({"movie_id": movie["_id"]})
    db.movies.delete_one({"_id": movie["_id"]})
    return redirect("/admin/movies")


# ------------------------- REST API ROUTES -------------------------


@app.get("/api/movies", tags=["Movies"])
def api_list_movies(search: str = ""):
    if search.strip():
        movies = list(
            db.movies.find(
                {"$text": {"$search": search.strip()}},
                {"score": {"$meta": "textScore"}},
            ).sort([("score", {"$meta": "textScore"})])
        )
    else:
        movies = list(db.movies.find().sort("created_at", -1))
    return {"items": serialize_doc(movies), "count": len(movies)}


@app.post("/api/movies", tags=["Movies"], status_code=201)
def api_create_movie(payload: MovieCreate, request: Request):
    require_api_admin(request, db)
    data = payload.model_dump()
    data["created_at"] = datetime.utcnow()
    result = db.movies.insert_one(data)
    created = db.movies.find_one({"_id": result.inserted_id})
    return serialize_doc(created)


@app.get("/api/movies/{movie_id}", tags=["Movies"])
def api_get_movie(movie_id: str):
    movie = get_movie_or_404(movie_id)
    screenings = list(db.screenings.find({"movie_id": movie["_id"]}).sort("starts_at", 1))
    result = serialize_doc(movie)
    result["screenings"] = serialize_doc(screenings)
    return result


@app.put("/api/movies/{movie_id}", tags=["Movies"])
def api_update_movie(movie_id: str, payload: MovieUpdate, request: Request):
    require_api_admin(request, db)
    movie = get_movie_or_404(movie_id)
    data = {key: value for key, value in payload.model_dump().items() if value is not None}
    if not data:
        return serialize_doc(movie)
    data["updated_at"] = datetime.utcnow()
    db.movies.update_one({"_id": movie["_id"]}, {"$set": data})
    return serialize_doc(db.movies.find_one({"_id": movie["_id"]}))


@app.delete("/api/movies/{movie_id}", tags=["Movies"])
def api_delete_movie(movie_id: str, request: Request):
    require_api_admin(request, db)
    movie = get_movie_or_404(movie_id)
    db.screenings.delete_many({"movie_id": movie["_id"]})
    db.ticket_orders.delete_many({"movie_id": movie["_id"]})
    db.movies.delete_one({"_id": movie["_id"]})
    return {"status": "deleted", "movie_id": movie_id}


@app.post("/api/orders", tags=["Orders"], status_code=201)
def api_create_order(payload: OrderCreate, request: Request):
    user = require_api_user(request, db)
    screening = get_screening_or_404(payload.screening_id)
    updated_screening = db.screenings.find_one_and_update(
        {"_id": screening["_id"], "available_seats": {"$gte": payload.seats_count}},
        {"$inc": {"available_seats": -payload.seats_count}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated_screening:
        raise HTTPException(status_code=400, detail="Недостатньо доступних місць")
    movie = db.movies.find_one({"_id": updated_screening["movie_id"]})
    order = {
        "user_id": user["_id"],
        "user_email": user["email"],
        "movie_id": movie["_id"],
        "screening_id": updated_screening["_id"],
        "movie_title": movie["title"],
        "screening": {
            "starts_at": updated_screening["starts_at"],
            "hall": updated_screening["hall"],
            "price": updated_screening["price"],
        },
        "seats_count": payload.seats_count,
        "total_price": payload.seats_count * int(updated_screening["price"]),
        "status": "confirmed",
        "created_at": datetime.utcnow(),
    }
    result = db.ticket_orders.insert_one(order)
    return serialize_doc(db.ticket_orders.find_one({"_id": result.inserted_id}))


@app.get("/api/my-orders", tags=["Orders"])
def api_my_orders(request: Request):
    user = require_api_user(request, db)
    orders = list(db.ticket_orders.find({"user_id": user["_id"]}).sort("created_at", -1))
    return {"items": serialize_doc(orders), "count": len(orders)}


@app.get("/api/mongodb/search", tags=["MongoDB"])
def api_text_search(query: str):
    """MongoDB text search across title, genre and description."""
    if not query.strip():
        return {"items": [], "count": 0}
    movies = list(
        db.movies.find(
            {"$text": {"$search": query.strip()}},
            {"score": {"$meta": "textScore"}},
        ).sort([("score", {"$meta": "textScore"})])
    )
    return {"items": serialize_doc(movies), "count": len(movies)}


@app.get("/api/mongodb/statistics/orders-by-movie", tags=["MongoDB"])
def api_orders_statistics():
    """Aggregation pipeline: revenue and ticket count grouped by movie."""
    stats = list(
        db.ticket_orders.aggregate(
            [
                {
                    "$group": {
                        "_id": "$movie_id",
                        "movie_title": {"$first": "$movie_title"},
                        "orders_count": {"$sum": 1},
                        "tickets": {"$sum": "$seats_count"},
                        "revenue": {"$sum": "$total_price"},
                    }
                },
                {"$sort": {"revenue": -1}},
            ]
        )
    )
    return {"items": serialize_doc(stats), "count": len(stats)}
