# Лабораторна робота №3

## Тема
**Міграція проєкту «Замовлення квитків у кінотеатр» на MongoDB**

Проєкт розроблено на Python з використанням FastAPI, Jinja2, MongoDB та бібліотеки `pymongo`.

## Що реалізовано

1. Серверна генерація HTML-сторінок через Jinja2.
2. Збереження даних у MongoDB.
3. Доступ до MongoDB через `pymongo`.
4. Ролі користувачів: `admin` та `user`.
5. CRUD-операції для сутності `Movie`.
6. Змінена OpenAPI-документація.
7. Новий функціонал MongoDB:
   - text index і текстовий пошук фільмів;
   - aggregation pipeline для статистики продажів;
   - embedded document у замовленні квитка;
   - atomic update кількості доступних місць.

## Колекції MongoDB

- `users`
- `movies`
- `screenings`
- `ticket_orders`

## Дані для входу

Адміністратор:

```text
email: admin@cinema.local
password: admin123
```

Користувач:

```text
email: user@cinema.local
password: user123
```

## Варіант 1. Запуск через Docker Compose

У корені проєкту виконайте:

```bash
docker compose up --build
```

Після запуску відкрийте:

```text
http://127.0.0.1:8000
```

OpenAPI/Swagger:

```text
http://127.0.0.1:8000/docs
```

MongoDB буде доступна всередині Docker Compose за адресою:

```text
mongodb://mongo:27017
```

## Варіант 2. Локальний запуск без Docker для Python-застосунку

Спочатку потрібно мати запущену MongoDB локально на порту `27017`.

Потім виконайте:

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Основні сторінки

```text
/                  головна сторінка
/register           реєстрація користувача
/login              авторизація
/movies             каталог фільмів і MongoDB text search
/my-orders          замовлення користувача
/admin              адмінпанель
/admin/movies       CRUD для Movie
/docs               OpenAPI-документація
```

## REST API

```text
GET     /api/movies
POST    /api/movies
GET     /api/movies/{movie_id}
PUT     /api/movies/{movie_id}
DELETE  /api/movies/{movie_id}
POST    /api/orders
GET     /api/my-orders
GET     /api/mongodb/search
GET     /api/mongodb/statistics/orders-by-movie
```

## Примітка

Під час першого запуску застосунок автоматично створює індекси MongoDB, адміністратора, тестового користувача, фільми та сеанси.
