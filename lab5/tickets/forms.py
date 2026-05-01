import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Hall, Movie, Screening, TicketOrder


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(label='Email', required=True)
    first_name = forms.CharField(label='Ім’я', max_length=100, required=False)
    last_name = forms.CharField(label='Прізвище', max_length=100, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError('Користувач із таким email уже існує.')
        return email


class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = ['title', 'genre', 'duration_minutes', 'age_rating', 'description', 'poster_url']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if len(title) < 2:
            raise ValidationError('Назва фільму має містити щонайменше 2 символи.')
        return title

    def clean_duration_minutes(self):
        duration = self.cleaned_data['duration_minutes']
        if duration < 30 or duration > 300:
            raise ValidationError('Тривалість фільму має бути від 30 до 300 хвилин.')
        return duration


class HallForm(forms.ModelForm):
    class Meta:
        model = Hall
        fields = ['name', 'rows', 'seats_per_row', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_rows(self):
        rows = self.cleaned_data['rows']
        if rows < 1 or rows > 50:
            raise ValidationError('Кількість рядів має бути від 1 до 50.')
        return rows

    def clean_seats_per_row(self):
        seats = self.cleaned_data['seats_per_row']
        if seats < 1 or seats > 50:
            raise ValidationError('Кількість місць у ряду має бути від 1 до 50.')
        return seats


class ScreeningForm(forms.ModelForm):
    class Meta:
        model = Screening
        fields = ['movie', 'hall', 'start_time', 'price', 'is_active']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_time'].input_formats = ['%Y-%m-%dT%H:%M']

    def clean_start_time(self):
        start_time = self.cleaned_data['start_time']
        if start_time < timezone.now() - timezone.timedelta(days=1):
            raise ValidationError('Не можна створювати сеанс у минулому.')
        return start_time

    def clean_price(self):
        price = self.cleaned_data['price']
        if price <= 0:
            raise ValidationError('Ціна квитка повинна бути більшою за 0.')
        return price


class TicketOrderForm(forms.ModelForm):
    class Meta:
        model = TicketOrder
        fields = ['customer_name', 'email', 'phone', 'seats_count', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_customer_name(self):
        name = self.cleaned_data['customer_name'].strip()
        if len(name) < 2:
            raise ValidationError('Ім’я клієнта має містити щонайменше 2 символи.')
        return name

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if not re.match(r'^\+?[0-9\s\-()]{7,20}$', phone):
            raise ValidationError('Введіть коректний номер телефону.')
        return phone

    def clean_seats_count(self):
        seats_count = self.cleaned_data['seats_count']
        if seats_count < 1 or seats_count > 10:
            raise ValidationError('Кількість квитків має бути від 1 до 10.')
        return seats_count


class TicketOrderAdminForm(TicketOrderForm):
    class Meta(TicketOrderForm.Meta):
        model = TicketOrder
        fields = ['customer_name', 'email', 'phone', 'seats_count', 'status', 'comment']
