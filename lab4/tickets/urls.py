from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.index, name='index'),
    path('movies/', views.movies, name='movies'),
    path('movies/<int:movie_id>/', views.movie_detail, name='movie_detail'),
    path('screenings/', views.screenings, name='screenings'),
    path('order/<int:screening_id>/', views.order_ticket, name='order_ticket'),
    path('about/', views.about, name='about'),
]
