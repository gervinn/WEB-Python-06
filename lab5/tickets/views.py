from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import HallForm, MovieForm, RegistrationForm, ScreeningForm, TicketOrderAdminForm, TicketOrderForm
from .models import Hall, Movie, Screening, TicketOrder


def is_admin(user):
    return user.is_authenticated and user.is_staff


def admin_required(view_func):
    return user_passes_test(is_admin, login_url='login')(view_func)


def index(request):
    movies_count = Movie.objects.count()
    screenings_count = Screening.objects.filter(is_active=True).count()
    orders_count = TicketOrder.objects.count() if request.user.is_staff else None
    latest_movies = Movie.objects.all()[:3]
    context = {
        'movies_count': movies_count,
        'screenings_count': screenings_count,
        'orders_count': orders_count,
        'latest_movies': latest_movies,
    }
    return render(request, 'tickets/index.html', context)


def about(request):
    return render(request, 'tickets/about.html')


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Реєстрацію виконано успішно.')
            return redirect('index')
    else:
        form = RegistrationForm()
    return render(request, 'tickets/register.html', {'form': form})


# -------------------- Movie CRUD --------------------

def movie_list(request):
    query = request.GET.get('q', '').strip()
    movies = Movie.objects.all()
    if query:
        movies = movies.filter(title__icontains=query) | movies.filter(genre__icontains=query)
    return render(request, 'tickets/movie_list.html', {'movies': movies, 'query': query})


def movie_detail(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    screenings = movie.screenings.filter(is_active=True, start_time__gte=timezone.now()).select_related('hall')
    return render(request, 'tickets/movie_detail.html', {'movie': movie, 'screenings': screenings})


@admin_required
def movie_create(request):
    if request.method == 'POST':
        form = MovieForm(request.POST)
        if form.is_valid():
            movie = form.save()
            messages.success(request, 'Фільм успішно створено.')
            return redirect('movie_detail', pk=movie.pk)
    else:
        form = MovieForm()
    return render(request, 'tickets/form.html', {'form': form, 'title': 'Створення фільму'})


@admin_required
def movie_update(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    if request.method == 'POST':
        form = MovieForm(request.POST, instance=movie)
        if form.is_valid():
            form.save()
            messages.success(request, 'Фільм успішно оновлено.')
            return redirect('movie_detail', pk=movie.pk)
    else:
        form = MovieForm(instance=movie)
    return render(request, 'tickets/form.html', {'form': form, 'title': 'Редагування фільму'})


@admin_required
def movie_delete(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    if request.method == 'POST':
        movie.delete()
        messages.success(request, 'Фільм успішно видалено.')
        return redirect('movie_list')
    return render(request, 'tickets/confirm_delete.html', {'object': movie, 'title': 'Видалення фільму'})


# -------------------- Hall CRUD --------------------

def hall_list(request):
    halls = Hall.objects.all()
    return render(request, 'tickets/hall_list.html', {'halls': halls})


def hall_detail(request, pk):
    hall = get_object_or_404(Hall, pk=pk)
    screenings = hall.screenings.select_related('movie').all()
    return render(request, 'tickets/hall_detail.html', {'hall': hall, 'screenings': screenings})


@admin_required
def hall_create(request):
    if request.method == 'POST':
        form = HallForm(request.POST)
        if form.is_valid():
            hall = form.save()
            messages.success(request, 'Кінозал успішно створено.')
            return redirect('hall_detail', pk=hall.pk)
    else:
        form = HallForm()
    return render(request, 'tickets/form.html', {'form': form, 'title': 'Створення кінозалу'})


@admin_required
def hall_update(request, pk):
    hall = get_object_or_404(Hall, pk=pk)
    if request.method == 'POST':
        form = HallForm(request.POST, instance=hall)
        if form.is_valid():
            form.save()
            messages.success(request, 'Дані кінозалу оновлено.')
            return redirect('hall_detail', pk=hall.pk)
    else:
        form = HallForm(instance=hall)
    return render(request, 'tickets/form.html', {'form': form, 'title': 'Редагування кінозалу'})


@admin_required
def hall_delete(request, pk):
    hall = get_object_or_404(Hall, pk=pk)
    if request.method == 'POST':
        hall.delete()
        messages.success(request, 'Кінозал видалено.')
        return redirect('hall_list')
    return render(request, 'tickets/confirm_delete.html', {'object': hall, 'title': 'Видалення кінозалу'})


# -------------------- Screening CRUD --------------------

def screening_list(request):
    screenings = Screening.objects.select_related('movie', 'hall').all()
    if not request.user.is_staff:
        screenings = screenings.filter(is_active=True)
    return render(request, 'tickets/screening_list.html', {'screenings': screenings})


def screening_detail(request, pk):
    screening = get_object_or_404(Screening.objects.select_related('movie', 'hall'), pk=pk)
    return render(request, 'tickets/screening_detail.html', {'screening': screening})


@admin_required
def screening_create(request):
    if request.method == 'POST':
        form = ScreeningForm(request.POST)
        if form.is_valid():
            screening = form.save()
            messages.success(request, 'Сеанс успішно створено.')
            return redirect('screening_detail', pk=screening.pk)
    else:
        form = ScreeningForm()
    return render(request, 'tickets/form.html', {'form': form, 'title': 'Створення сеансу'})


@admin_required
def screening_update(request, pk):
    screening = get_object_or_404(Screening, pk=pk)
    if request.method == 'POST':
        form = ScreeningForm(request.POST, instance=screening)
        if form.is_valid():
            form.save()
            messages.success(request, 'Сеанс успішно оновлено.')
            return redirect('screening_detail', pk=screening.pk)
    else:
        form = ScreeningForm(instance=screening)
    return render(request, 'tickets/form.html', {'form': form, 'title': 'Редагування сеансу'})


@admin_required
def screening_delete(request, pk):
    screening = get_object_or_404(Screening, pk=pk)
    if request.method == 'POST':
        screening.delete()
        messages.success(request, 'Сеанс видалено.')
        return redirect('screening_list')
    return render(request, 'tickets/confirm_delete.html', {'object': screening, 'title': 'Видалення сеансу'})


# -------------------- TicketOrder CRUD --------------------

@login_required
def order_list(request):
    if request.user.is_staff:
        orders = TicketOrder.objects.select_related('user', 'screening__movie', 'screening__hall').all()
        stats = orders.aggregate(total_tickets=Sum('seats_count'), orders_count=Count('id'), income=Sum('total_price'))
    else:
        orders = TicketOrder.objects.select_related('screening__movie', 'screening__hall').filter(user=request.user)
        stats = None
    return render(request, 'tickets/order_list.html', {'orders': orders, 'stats': stats})


@login_required
def order_create(request, screening_id):
    screening = get_object_or_404(Screening.objects.select_related('movie', 'hall'), pk=screening_id, is_active=True)
    initial = {
        'customer_name': request.user.get_full_name() or request.user.username,
        'email': request.user.email,
    }
    if request.method == 'POST':
        form = TicketOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.screening = screening
            order.save()
            messages.success(request, 'Замовлення успішно створено.')
            return redirect('order_detail', pk=order.pk)
    else:
        form = TicketOrderForm(initial=initial)
    return render(request, 'tickets/order_form.html', {'form': form, 'screening': screening, 'title': 'Оформлення замовлення'})


def get_order_for_user(request, pk):
    order = get_object_or_404(TicketOrder.objects.select_related('user', 'screening__movie', 'screening__hall'), pk=pk)
    if not request.user.is_staff and order.user != request.user:
        raise PermissionDenied('Ви не маєте доступу до цього замовлення.')
    return order


@login_required
def order_detail(request, pk):
    order = get_order_for_user(request, pk)
    return render(request, 'tickets/order_detail.html', {'order': order})


@login_required
def order_update(request, pk):
    order = get_order_for_user(request, pk)
    form_class = TicketOrderAdminForm if request.user.is_staff else TicketOrderForm
    if request.method == 'POST':
        form = form_class(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Замовлення оновлено.')
            return redirect('order_detail', pk=order.pk)
    else:
        form = form_class(instance=order)
    return render(request, 'tickets/order_form.html', {'form': form, 'screening': order.screening, 'title': 'Редагування замовлення'})


@login_required
def order_delete(request, pk):
    order = get_order_for_user(request, pk)
    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Замовлення видалено.')
        return redirect('order_list')
    return render(request, 'tickets/confirm_delete.html', {'object': order, 'title': 'Видалення замовлення'})
