from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Movie(models.Model):
    title = models.CharField('Назва фільму', max_length=150, unique=True)
    genre = models.CharField('Жанр', max_length=100)
    duration_minutes = models.PositiveIntegerField('Тривалість, хв')
    age_rating = models.CharField('Вікове обмеження', max_length=10, default='12+')
    description = models.TextField('Опис')
    poster_url = models.URLField('URL постера', blank=True)
    created_at = models.DateTimeField('Створено', auto_now_add=True)

    class Meta:
        ordering = ['title']
        verbose_name = 'Фільм'
        verbose_name_plural = 'Фільми'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('movie_detail', kwargs={'pk': self.pk})


class Hall(models.Model):
    name = models.CharField('Назва залу', max_length=100, unique=True)
    rows = models.PositiveIntegerField('Кількість рядів')
    seats_per_row = models.PositiveIntegerField('Місць у ряду')
    description = models.TextField('Опис залу', blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Кінозал'
        verbose_name_plural = 'Кінозали'

    @property
    def capacity(self):
        return self.rows * self.seats_per_row

    def __str__(self):
        return f'{self.name} ({self.capacity} місць)'


class Screening(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='screenings', verbose_name='Фільм')
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE, related_name='screenings', verbose_name='Кінозал')
    start_time = models.DateTimeField('Дата та час сеансу')
    price = models.DecimalField('Ціна квитка', max_digits=8, decimal_places=2)
    is_active = models.BooleanField('Активний сеанс', default=True)

    class Meta:
        ordering = ['start_time']
        constraints = [
            models.UniqueConstraint(fields=['hall', 'start_time'], name='unique_screening_hall_start_time')
        ]
        verbose_name = 'Сеанс'
        verbose_name_plural = 'Сеанси'

    def clean(self):
        if self.price is not None and self.price <= 0:
            raise ValidationError({'price': 'Ціна квитка повинна бути більшою за 0.'})
        if self.start_time and self.start_time < timezone.now() - timezone.timedelta(days=1):
            raise ValidationError({'start_time': 'Не можна створювати сеанс у минулому.'})

    def __str__(self):
        return f'{self.movie.title} — {self.start_time:%d.%m.%Y %H:%M}'


class TicketOrder(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Очікує оплати'),
        (STATUS_PAID, 'Оплачено'),
        (STATUS_CANCELLED, 'Скасовано'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ticket_orders', verbose_name='Користувач')
    screening = models.ForeignKey(Screening, on_delete=models.CASCADE, related_name='orders', verbose_name='Сеанс')
    customer_name = models.CharField('Ім’я клієнта', max_length=120)
    email = models.EmailField('Email')
    phone = models.CharField('Телефон', max_length=20)
    seats_count = models.PositiveIntegerField('Кількість квитків')
    total_price = models.DecimalField('Загальна сума', max_digits=9, decimal_places=2, default=0)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    comment = models.TextField('Коментар', blank=True)
    created_at = models.DateTimeField('Дата створення', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Замовлення квитків'
        verbose_name_plural = 'Замовлення квитків'

    def clean(self):
        if self.seats_count is not None and not (1 <= self.seats_count <= 10):
            raise ValidationError({'seats_count': 'За одне замовлення можна придбати від 1 до 10 квитків.'})
        if self.screening_id and not self.screening.is_active:
            raise ValidationError({'screening': 'Для неактивного сеансу неможливо оформити замовлення.'})

    def save(self, *args, **kwargs):
        if self.screening_id and self.seats_count:
            self.total_price = Decimal(self.seats_count) * self.screening.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Замовлення #{self.pk} — {self.customer_name}'
