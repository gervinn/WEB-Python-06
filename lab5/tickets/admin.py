from django.contrib import admin

from .models import Hall, Movie, Screening, TicketOrder


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'genre', 'duration_minutes', 'age_rating')
    search_fields = ('title', 'genre')


@admin.register(Hall)
class HallAdmin(admin.ModelAdmin):
    list_display = ('name', 'rows', 'seats_per_row', 'capacity')


@admin.register(Screening)
class ScreeningAdmin(admin.ModelAdmin):
    list_display = ('movie', 'hall', 'start_time', 'price', 'is_active')
    list_filter = ('is_active', 'hall')


@admin.register(TicketOrder)
class TicketOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'screening', 'seats_count', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'email', 'phone')
