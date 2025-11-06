from django.db import transaction
from core.models import Basket, Order, OrderItem, Promocode
from v1.services.auth import authenticate_user

def create_order(request, params):
    try:
        user = authenticate_user(request)
        if not user:
            return {
                "error": "Пользователь не аутентифицирован",
                "order_id": None,
                "total_price": 0,
                "status": 401,
                "method": "create.order"
            }

        basket = Basket.objects.filter(user=user)
        if not basket.exists():
            return {
                "error": "Корзина пуста",
                "order_id": None,
                "total_price": 0,
                "status": 400,
                "method": "create.order"
            }

        total_price = 0
        for item in basket:
            total_price += int(item.total_price)

        promocode_discount = 0
        promocode_name = params.get("promocode_name")
        promocode = None
        applied_discount_type = "none"

        if promocode_name:
            promocode = Promocode.objects.filter(name=promocode_name, status=True).first()
            if promocode:
                promocode_discount = promocode.discount
                applied_discount_type = "promocode"
        else:
            if total_price > 20000:
                promocode_discount = 15
                applied_discount_type = "auto_15_percent"
            elif total_price > 7000:
                promocode_discount = 10
                applied_discount_type = "auto_10_percent"
            elif total_price > 3000:
                promocode_discount = 5
                applied_discount_type = "auto_5_percent"

        discounted_total = int(total_price * (1 - promocode_discount / 100))

        with transaction.atomic():
            order = Order(user=user, promocode=promocode)
            order.save()

            order_items = []
            for basket_item in basket:
                order_item = OrderItem(
                    order=order,
                    product=basket_item.product,
                    quantity=basket_item.quantity,
                    discount=promocode_discount
                )
                order_item.save()
                order_items.append({
                    "product_id": basket_item.product.id,
                    "quantity": basket_item.quantity,
                    "discount": promocode_discount,
                    "total_item_price": int(int(basket_item.total_price) * (1 - promocode_discount / 100))
                })

            basket.delete()

        return {
            "order_id": order.id,
            "items": order_items,
            "total_price": discounted_total,
            "promocode_applied": promocode_discount > 0,
            "discount_type": applied_discount_type,
            "message": "Заказ оформлен успешно",
            "status": 200,
            "method": "create.order"
        }

    except Exception as e:
        return {
            "error": str(e),
            "order_id": None,
            "total_price": 0,
            "status": 500,
            "method": "create.order"
        }