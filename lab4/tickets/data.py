MOVIES = [
    {
        'id': 1,
        'title': 'Дюна: Частина друга',
        'genre': 'Фантастика',
        'duration': 166,
        'age_limit': '12+',
        'poster': 'https://static.sweet.tv/images/cache/v2/movie_horizontal_poster/CN_UARICdWsaAlVBIAIoFg==/267642-dyuna-chastina-druga_.jpg',
        'description': 'Продовження історії Пола Атріда, який об’єднується з фременами та бореться за майбутнє Арракіса.',
    },
    {
        'id': 2,
        'title': 'Думками навиворіт 2',
        'genre': 'Анімація',
        'duration': 96,
        'age_limit': '0+',
        'poster': 'https://kinoafisha.ua/upload/2023/11/films/10205/26jvfr73dumkami-navivorit-2.jpg',
        'description': 'Анімаційна історія про нові емоції, дорослішання та внутрішній світ головної героїні.',
    },
    {
        'id': 3,
        'title': 'Каскадер',
        'genre': 'Екшн',
        'duration': 126,
        'age_limit': '16+',
        'poster': 'https://superkomp.com.ua/wp-content/uploads/kaskader_poster.jpg',
        'description': 'Історія каскадера, який повертається до роботи та опиняється у центрі небезпечної пригоди.',
    },
    {
        'id': 4,
        'title': 'Кінотеатр мрій',
        'genre': 'Драма',
        'duration': 112,
        'age_limit': '12+',
        'poster': 'https://www.kinofilms.ua/images/videos/mainpage/38442.jpg',
        'description': 'Фільм про маленький кінотеатр, який стає місцем зустрічі різних людей та історій.',
    },
]

SCREENINGS = [
    {'id': 1, 'movie_id': 1, 'hall': 'Зал 1', 'date': '2026-05-02', 'time': '18:30', 'price': 180},
    {'id': 2, 'movie_id': 1, 'hall': 'Зал 2', 'date': '2026-05-02', 'time': '21:10', 'price': 210},
    {'id': 3, 'movie_id': 2, 'hall': 'Зал 3', 'date': '2026-05-03', 'time': '15:00', 'price': 150},
    {'id': 4, 'movie_id': 3, 'hall': 'Зал 1', 'date': '2026-05-03', 'time': '19:40', 'price': 190},
    {'id': 5, 'movie_id': 4, 'hall': 'Зал 4', 'date': '2026-05-04', 'time': '17:20', 'price': 160},
]


def get_movie(movie_id: int):
    return next((movie for movie in MOVIES if movie['id'] == movie_id), None)


def get_screening(screening_id: int):
    return next((screening for screening in SCREENINGS if screening['id'] == screening_id), None)


def get_screenings_for_movie(movie_id: int):
    return [screening for screening in SCREENINGS if screening['movie_id'] == movie_id]


def enrich_screenings():
    result = []
    for screening in SCREENINGS:
        result.append({**screening, 'movie': get_movie(screening['movie_id'])})
    return result
