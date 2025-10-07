from core.models import Product
from django.core.cache import cache

def get_home_page_products(request, params):
    cache_key = "home_page_products"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data

    most_selled = (
        Product.objects.order_by("-selled")[:5]
        .values("id", "name", "price", "discount", "price_type", "selled", "created_at", "updated_at")
    )

    new_products = (
        Product.objects.order_by("-created_at")[:5]
        .values("id", "name", "price", "discount", "price_type", "selled", "created_at", "updated_at")
    )

    data = {
        "most_selled": list(most_selled),
        "new": list(new_products),
    }

    cache.set(cache_key, data, timeout=300)

    return data
