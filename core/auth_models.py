from functools import lru_cache
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
import urllib.request
import json
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, phone, username, password=None, **extra_fields):
        if not phone:
            raise ValueError(_('The Phone field must be set'))
        if not username:
            raise ValueError(_('The Username field must be set'))

        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', False)

        user = self.model(phone=phone, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 2)  # admin

        return self.create_user(phone, username, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(_("Ism familiya"), max_length=50)
    phone = models.CharField(_("Telefon raqam"), max_length=12, unique=True)
    place = models.CharField(max_length=512)
    email = models.EmailField()
    user_type = models.SmallIntegerField(default=1, choices=[
        (1, 'user'),
        (2, 'admin')
    ])
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    
    objects = CustomUserManager()
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['username', 'user_type']

    def __str__(self):
        return self.username

    @lru_cache(maxsize=1)
    def get_exchange_rates(self):
        rates = cache.get("exchange_rates")
        if not rates:
            try:
                with urllib.request.urlopen("https://cbu.uz/oz/arkhiv-kursov-valyut/json/") as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode('utf-8'))
                        usd = next(item for item in data if item["Ccy"] == "USD")["Rate"]
                        rub = next(item for item in data if item["Ccy"] == "RUB")["Rate"]

                        rates = {
                            "USD": float(usd),
                            "RUB": float(rub),
                            "UZS": 1.0
                        }
                        cache.set("exchange_rates", rates, 60 * 60)
            except Exception:
                rates = {
                    "USD": 12800.0,
                    "RUB": 163.0,
                    "UZS": 1.0
                }
        return rates

    def calculate_cart(self):
        carts = self.carts.filter(status=True)
        total_balance = 0.0
        rates = self.get_exchange_rates()
        for cart in carts:
            cart_total = cart.total_price
            price_type = cart.product.price_type
            total_balance += cart_total * rates[price_type]
        usd_total = total_balance / rates["UZS"]
        return f"{usd_total:.2f} sum"