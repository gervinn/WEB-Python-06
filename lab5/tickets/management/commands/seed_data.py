from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from tickets.models import Hall, Movie, Screening, TicketOrder


class Command(BaseCommand):
    help = 'Створює тестові дані для лабораторної роботи №5'

    def handle(self, *args, **options):
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@cinema.local', 'is_staff': True, 'is_superuser': True, 'first_name': 'Admin'},
        )
        if created:
            admin.set_password('admin123')
            admin.save()

        user, created = User.objects.get_or_create(
            username='user',
            defaults={'email': 'user@cinema.local', 'first_name': 'Cinema', 'last_name': 'User'},
        )
        if created:
            user.set_password('user123')
            user.save()

        hall1, _ = Hall.objects.get_or_create(name='Зал 1', defaults={'rows': 10, 'seats_per_row': 12, 'description': 'Основний зал з великим екраном.'})
        hall2, _ = Hall.objects.get_or_create(name='VIP-зал', defaults={'rows': 6, 'seats_per_row': 8, 'description': 'Комфортний зал з покращеними кріслами.'})

        movies_data = [
            {
                'title': 'Дюна: Частина друга',
                'genre': 'Фантастика',
                'duration_minutes': 166,
                'age_rating': '12+',
                'description': 'Епічна історія про боротьбу за владу, ресурси та майбутнє планети Арракіс.',
                'poster_url': 'https://placehold.co/600x850?text=Dune+2',
            },
            {
                'title': 'Думками навиворіт 2',
                'genre': 'Анімація',
                'duration_minutes': 96,
                'age_rating': '0+',
                'description': 'Анімаційний фільм про емоції, дорослішання та нові життєві виклики.',
                'poster_url': 'https://placehold.co/600x850?text=Inside+Out+2',
            },
            {
                'title': 'Каскадер',
                'genre': 'Екшн',
                'duration_minutes': 126,
                'age_rating': '16+',
                'description': 'Динамічна історія про каскадера, ризик, кіноіндустрію та несподівані пригоди.',
                'poster_url': 'https://placehold.co/600x850?text=Action+Movie',
            },
        ]

        movies = []
        for item in movies_data:
            movie, _ = Movie.objects.get_or_create(title=item['title'], defaults=item)
            movies.append(movie)

        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        for index, movie in enumerate(movies):
            Screening.objects.get_or_create(
                movie=movie,
                hall=hall1 if index % 2 == 0 else hall2,
                start_time=now + timezone.timedelta(days=index + 1, hours=18),
                defaults={'price': Decimal('180.00') + Decimal(index * 25), 'is_active': True},
            )

        screening = Screening.objects.first()
        if screening and not TicketOrder.objects.filter(user=user).exists():
            TicketOrder.objects.create(
                user=user,
                screening=screening,
                customer_name='Cinema User',
                email='user@cinema.local',
                phone='+380501112233',
                seats_count=2,
                status=TicketOrder.STATUS_PENDING,
                comment='Тестове замовлення для демонстрації CRUD.',
            )

        self.stdout.write(self.style.SUCCESS('Тестові дані створено успішно.'))
        self.stdout.write('Admin: admin / admin123')
        self.stdout.write('User: user / user123')
