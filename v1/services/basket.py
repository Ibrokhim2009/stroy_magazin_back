


from core.models import Basket, Product
from v1.services.auth import authenticate_user


def get_basket(request, params):
    """
    Возвращает содержимое корзины текущего пользователя.
    """
    user = authenticate_user(request)
    if not user:
        return {"response": {"error": "Требуется аутентификация"}, "status": 401}

    try:
        basket_items_qs = Basket.objects.filter(user=user)
        basket_items = []
        total_price = 0
        for item in basket_items_qs:
            item_data = {
                "product_id": item.product.id,
                "product_name": item.product.name,
                "quantity": item.quantity,
                "price_per_item": item.product.get_price(),
                "total_item_price": int(item.total_price),
            }
            basket_items.append(item_data)
            total_price += int(item.total_price)

        return {
            "response": {
                "success": "Корзина получена",
                "data": {"basket_items": basket_items, "total_price": total_price}
            },
            "status": 200
        }
    except Exception as e:
        return {"response": {"error": "Ошибка при получении корзины"}, "status": 500}

def add_to_basket(request, params):
    """
    Добавляет продукт в корзину, если его нет, или удаляет, если есть.
    """
    user = authenticate_user(request)
    if not user:
        return {"response": {"error": "Требуется аутентификация"}, "status": 401}

    product_id = params.get("product_id")
    quantity = params.get("quantity", 1)

    if not product_id:
        return {"response": {"error": "Отсутствует product_id"}, "status": 400}

    try:
        product_id = int(product_id)
        quantity = int(quantity)
    except ValueError:
        return {"response": {"error": "Недопустимый формат product_id или quantity"}, "status": 400}

    try:
        product = Product.objects.filter(id=product_id).first()
        if not product:
            return {"response": {"error": "Продукт не найден"}, "status": 404}

        basket_item = Basket.objects.filter(user=user, product=product).first()

        if basket_item:
            basket_item.delete()
            message = "Продукт удален из корзины"
        else:
            basket_item = Basket(user=user, product=product, quantity=quantity)
            basket_item.save()
            message = "Продукт добавлен в корзину"

        # Возвращаем обновленную корзину
        basket_response = get_basket(request, {})
        basket_response["response"]["message"] = message
        return basket_response

    except Exception as e:
        return {"response": {"error": "Ошибка при обработке корзины"}, "status": 500}

