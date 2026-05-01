from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='tickets/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('movies/', views.movie_list, name='movie_list'),
    path('movies/create/', views.movie_create, name='movie_create'),
    path('movies/<int:pk>/', views.movie_detail, name='movie_detail'),
    path('movies/<int:pk>/edit/', views.movie_update, name='movie_update'),
    path('movies/<int:pk>/delete/', views.movie_delete, name='movie_delete'),

    path('halls/', views.hall_list, name='hall_list'),
    path('halls/create/', views.hall_create, name='hall_create'),
    path('halls/<int:pk>/', views.hall_detail, name='hall_detail'),
    path('halls/<int:pk>/edit/', views.hall_update, name='hall_update'),
    path('halls/<int:pk>/delete/', views.hall_delete, name='hall_delete'),

    path('screenings/', views.screening_list, name='screening_list'),
    path('screenings/create/', views.screening_create, name='screening_create'),
    path('screenings/<int:pk>/', views.screening_detail, name='screening_detail'),
    path('screenings/<int:pk>/edit/', views.screening_update, name='screening_update'),
    path('screenings/<int:pk>/delete/', views.screening_delete, name='screening_delete'),

    path('orders/', views.order_list, name='order_list'),
    path('orders/create/<int:screening_id>/', views.order_create, name='order_create'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/edit/', views.order_update, name='order_update'),
    path('orders/<int:pk>/delete/', views.order_delete, name='order_delete'),
]
