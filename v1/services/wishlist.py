from core.models import Features, Product, Wishlist
from v1.services.auth import authenticate_user


def get_wishlist(request, params):

    user = authenticate_user(request)
    if not user:
        return {"response": {"error": "Требуется аутентификация"}, "status": 401}

    try:
        wishlist_items_qs = Wishlist.objects.filter(user=user).prefetch_related("product__features")
        wishlist_items = []
        for item in wishlist_items_qs:
            product = item.product
            product_data = {
                "product_id": product.id,
                "name": product.name,
                "price": product.price,
                "discount": product.discount,
                "price_type": product.price_type,
                "selled": product.selled,
                "created_at": product.created_at,
                "updated_at": product.updated_at,
                "features": list(Features.objects.filter(product=product).values("key", "value"))
            }
            wishlist_items.append(product_data)

        return {
            "response": {
                "success": "Wishlist получен",
                "data": {"wishlist_items": wishlist_items}
            },
            "status": 200
        }
    except Exception as e:
        return {"response": {"error": "Ошибка при получении wishlist"}, "status": 500}
    
    
    
def add_wishlist(request, params):
    user = authenticate_user(request)
    if not user:
        return {"response": {"error": "Требуется аутентификация"}, "status": 401}

    product_id = params.get("product_id")
    if not product_id:
        return {"response": {"error": "Отсутствует product_id"}, "status": 400}

    try:
        product_id = int(product_id)
    except ValueError:
        return {"response": {"error": "Недопустимый формат product_id"}, "status": 400}

    try:
        product = Product.objects.filter(id=product_id).first()
        if not product:
            return {"response": {"error": "Продукт не найден"}, "status": 404}

        wishlist_item = Wishlist.objects.filter(user=user, product=product).first()

        if wishlist_item:
            wishlist_item.delete()
            message = "Продукт удален из wishlist"
        else:
            wishlist_item = Wishlist(user=user, product=product)
            wishlist_item.save()
            message = "Продукт добавлен в wishlist"

        wishlist_response = get_wishlist(request, {})
        wishlist_response["response"]["message"] = message
        return wishlist_response

    except Exception as e:
        return {"response": {"error": "Ошибка при обработке wishlist"}, "status": 500}