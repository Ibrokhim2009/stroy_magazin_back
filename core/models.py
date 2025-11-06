from django.db import models
from core.auth_models import User
import os
import uuid

def product_image_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("products", new_filename)

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    image = models.ImageField(upload_to="categories/", null=True, blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=256)
    price = models.IntegerField(default=0)
    discount = models.IntegerField(default=0)
    price_type = models.CharField(
        max_length=3,
        choices=[("UZS", "O'zbek so'mi"), ("USD", "Aqsh Dollori"), ("RUB", "Rossiya Rubli")],
        default="UZS",
    )
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING, related_name="product_category")
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    selled = models.IntegerField(default=0)

    def get_price(self):
        return int(self.price * (1 - self.discount / 100))

    def __str__(self):
        return self.name

    def get_price_with_icon(self):
        price = {
            "USD": f"{self.get_price()} $",
            "RUB": f"{self.get_price()} ₽",
            "UZS": f"{self.get_price()} So'm",
        }
        return price[self.price_type]

    def get_price_original_with_icon(self):
        price = {
            "USD": f"{self.price} $",
            "RUB": f"{self.price} ₽",
            "UZS": f"{self.price} So'm",
        }
        return price[self.price_type]

    def get_created(self):
        from django.utils.timezone import now
        created = self.created_at
        current = now()
        diff = (current - created).total_seconds()
        if diff < 60:
            return "Now"
        elif diff < 3600:
            minutes = int(diff // 60)
            return f"{minutes} minut oldin"
        elif diff < 86400:
            hours = int(diff // 3600)
            return f"{hours} soat oldin"
        else:
            return created.strftime("%d.%m.%Y %H:%M")

    def get_updated(self):
        from django.utils.timezone import now
        updated = self.updated_at
        current = now()
        diff = (current - updated).total_seconds()
        if diff < 60:
            return "Hozir"
        elif diff < 3600:
            minutes = int(diff // 60)
            return f"{minutes} minut oldin"
        elif diff < 86400:
            hours = int(diff // 3600)
            return f"{hours} soat oldin"
        else:
            return updated.strftime("%d.%m.%Y %H:%M")

    class Meta:
        db_table = 'core_product'
        indexes = [
            models.Index(fields=['selled']),
            models.Index(fields=['created_at']),
        ]

class Features(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="features")
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.product.name}: {self.key} = {self.value}"

    class Meta:
        verbose_name_plural = "Features"

class ProductImg(models.Model):
    date = models.DateField(null=True, blank=True)  # Made optional
    img = models.ImageField(upload_to=product_image_upload_path)
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, related_name='product_image')

class Basket(models.Model):
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0) 
    total_price = models.CharField(max_length=50, default='0')

    def save(self, *args, **kwargs):
        self.total_price = str(self.product.get_price() * self.quantity)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} → {self.product.name} x {self.quantity}" 

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user} ❤️ {self.product}"

class Promocode(models.Model):
    status = models.BooleanField(default=True)
    name = models.CharField(max_length=50)
    discount = models.IntegerField(default=0)

class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='items', blank=True,null=True )
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING)
    quantity = models.IntegerField(default=0)
    discount = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} x {self.quantity} (Order {self.order.id})"

class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    promocode = models.ForeignKey(Promocode, on_delete=models.DO_NOTHING, null=True, blank=True)
    
    def __str__(self):
        return f"Order {self.id} by {self.user}"
    
    
    
class Contact(models.Model):
    fio = models.CharField(default="Name Thename Father name", max_length=250)
    phone = models.CharField(default='+998999999999', max_length=20)
    message = models.TextField()