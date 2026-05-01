from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .data import MOVIES, SCREENINGS, enrich_screenings, get_movie, get_screening, get_screenings_for_movie


def index(request):
    return render(request, 'tickets/index.html', {
        'featured_movies': MOVIES[:3],
        'movies_count': len(MOVIES),
        'screenings_count': len(SCREENINGS),
    })


def movies(request):
    genre = request.GET.get('genre', '').strip()
    search = request.GET.get('search', '').strip().lower()
    filtered_movies = MOVIES

    if genre:
        filtered_movies = [movie for movie in filtered_movies if movie['genre'].lower() == genre.lower()]
    if search:
        filtered_movies = [
            movie for movie in filtered_movies
            if search in movie['title'].lower() or search in movie['description'].lower()
        ]

    return render(request, 'tickets/movies.html', {
        'movies': filtered_movies,
        'genres': sorted({movie['genre'] for movie in MOVIES}),
        'selected_genre': genre,
        'search': request.GET.get('search', ''),
    })


def movie_detail(request, movie_id):
    movie = get_movie(movie_id)
    if not movie:
        return render(request, 'tickets/not_found.html', {'message': 'Фільм не знайдено'}, status=404)

    return render(request, 'tickets/movie_detail.html', {
        'movie': movie,
        'screenings': get_screenings_for_movie(movie_id),
    })


def screenings(request):
    return render(request, 'tickets/screenings.html', {
        'screenings': enrich_screenings(),
    })


@require_http_methods(['GET', 'POST'])
def order_ticket(request, screening_id):
    screening = get_screening(screening_id)
    if not screening:
        return render(request, 'tickets/not_found.html', {'message': 'Сеанс не знайдено'}, status=404)

    movie = get_movie(screening['movie_id'])

    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', '').strip()
        email = request.POST.get('email', '').strip()
        seats = int(request.POST.get('seats', '1'))
        total_price = seats * screening['price']

        return render(request, 'tickets/order_success.html', {
            'customer_name': customer_name,
            'email': email,
            'seats': seats,
            'total_price': total_price,
            'screening': screening,
            'movie': movie,
        })

    return render(request, 'tickets/order_form.html', {
        'screening': screening,
        'movie': movie,
    })


def about(request):
    return render(request, 'tickets/about.html', {
        'technologies': ['Python', 'Django', 'Django Templates', 'HTML', 'CSS'],
        'routes': ['/', '/movies/', '/movies/<id>/', '/screenings/', '/order/<screening_id>/', '/about/'],
    })
