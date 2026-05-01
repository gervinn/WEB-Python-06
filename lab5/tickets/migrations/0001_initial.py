# Generated manually for laboratory project
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Hall',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Назва залу')),
                ('rows', models.PositiveIntegerField(verbose_name='Кількість рядів')),
                ('seats_per_row', models.PositiveIntegerField(verbose_name='Місць у ряду')),
                ('description', models.TextField(blank=True, verbose_name='Опис залу')),
            ],
            options={'verbose_name': 'Кінозал', 'verbose_name_plural': 'Кінозали', 'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150, unique=True, verbose_name='Назва фільму')),
                ('genre', models.CharField(max_length=100, verbose_name='Жанр')),
                ('duration_minutes', models.PositiveIntegerField(verbose_name='Тривалість, хв')),
                ('age_rating', models.CharField(default='12+', max_length=10, verbose_name='Вікове обмеження')),
                ('description', models.TextField(verbose_name='Опис')),
                ('poster_url', models.URLField(blank=True, verbose_name='URL постера')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Створено')),
            ],
            options={'verbose_name': 'Фільм', 'verbose_name_plural': 'Фільми', 'ordering': ['title']},
        ),
        migrations.CreateModel(
            name='Screening',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField(verbose_name='Дата та час сеансу')),
                ('price', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Ціна квитка')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активний сеанс')),
                ('hall', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='screenings', to='tickets.hall', verbose_name='Кінозал')),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='screenings', to='tickets.movie', verbose_name='Фільм')),
            ],
            options={'verbose_name': 'Сеанс', 'verbose_name_plural': 'Сеанси', 'ordering': ['start_time']},
        ),
        migrations.CreateModel(
            name='TicketOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_name', models.CharField(max_length=120, verbose_name='Ім’я клієнта')),
                ('email', models.EmailField(max_length=254, verbose_name='Email')),
                ('phone', models.CharField(max_length=20, verbose_name='Телефон')),
                ('seats_count', models.PositiveIntegerField(verbose_name='Кількість квитків')),
                ('total_price', models.DecimalField(decimal_places=2, default=0, max_digits=9, verbose_name='Загальна сума')),
                ('status', models.CharField(choices=[('pending', 'Очікує оплати'), ('paid', 'Оплачено'), ('cancelled', 'Скасовано')], default='pending', max_length=20, verbose_name='Статус')),
                ('comment', models.TextField(blank=True, verbose_name='Коментар')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата створення')),
                ('screening', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='tickets.screening', verbose_name='Сеанс')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ticket_orders', to=settings.AUTH_USER_MODEL, verbose_name='Користувач')),
            ],
            options={'verbose_name': 'Замовлення квитків', 'verbose_name_plural': 'Замовлення квитків', 'ordering': ['-created_at']},
        ),
        migrations.AddConstraint(
            model_name='screening',
            constraint=models.UniqueConstraint(fields=('hall', 'start_time'), name='unique_screening_hall_start_time'),
        ),
    ]
