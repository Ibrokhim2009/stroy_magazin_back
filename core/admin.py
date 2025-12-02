from django.contrib import admin

from core.auth_models import User
from core.models import Category, Features, Product, ProductImg, Promocode

# Register your models here.


admin.site.register(User)   
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductImg)
admin.site.register(Features)
admin.site.register(Promocode)