import logging
from core.models import Product, Features
from django.db.models import Q, ExpressionWrapper, IntegerField, F
from core.models import Product, Features
logger = logging.getLogger(__name__)

def get_home_page_products(request, params):
    try:
        most_selled_qs = (
            Product.objects.order_by("-selled")[:5]
            .prefetch_related("features")
            .values("id", "name", "price", "discount", "price_type", "selled", "created_at", "updated_at")
        )

        new_products_qs = (
            Product.objects.order_by("-created_at")[:5]
            .prefetch_related("features")
            .values("id", "name", "price", "discount", "price_type", "selled", "created_at", "updated_at")
        )

        most_selled = []
        for product in most_selled_qs:
            product_data = dict(product)
            features = Features.objects.filter(product_id=product["id"]).values("key", "value")
            product_data["features"] = list(features)
            most_selled.append(product_data)

        new_products = []
        for product in new_products_qs:
            product_data = dict(product)
            features = Features.objects.filter(product_id=product["id"]).values("key", "value")
            product_data["features"] = list(features)
            new_products.append(product_data)

        data = {
            "most_selled": most_selled,
            "new": new_products,
            "status": 200
        }

        return data

    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return {"most_selled": [], "new": []}
    
    
    
    
    
    



def get_and_filter_products(request, params):
    try:
        queryset = Product.objects.all()

        category_id = params.get("category_id")
        if category_id:
            try:
                queryset = queryset.filter(category=int(category_id))
            except ValueError:
                logger.warning(f"Недопустимый category_id: {category_id}")

        features = params.get("features", [])
        if features and isinstance(features, list):
            for feature in features:
                if isinstance(feature, dict) and "key" in feature and "value" in feature:
                    product_ids = Features.objects.filter(
                        key=feature["key"], value=feature["value"]
                    ).values_list("product_id", flat=True).distinct()
                    queryset = queryset.filter(id__in=product_ids)
                else:
                    logger.warning(f"Недопустимый формат характеристики: {feature}")

        min_price = params.get("min_price")
        max_price = params.get("max_price")
        if min_price or max_price:
            queryset = queryset.annotate(
                calculated_price=ExpressionWrapper(
                    F('price') * (1 - F('discount') / 100.0),
                    output_field=IntegerField()
                )
            )
            if min_price:
                queryset = queryset.filter(calculated_price__gte=int(min_price))
            if max_price:
                queryset = queryset.filter(calculated_price__lte=int(max_price))

        products_qs = (
            queryset.order_by("-selled") 
            .prefetch_related("features")
            .values("id", "name", "price", "discount", "price_type", "selled", "created_at", "updated_at")
        )

        products = []
        for product in products_qs:
            product_data = dict(product)
            features_qs = Features.objects.filter(product_id=product["id"]).values("key", "value")
            product_data["features"] = list(features_qs)
            products.append(product_data)

        return {"products": products}

    except Exception as e:
        logger.error(f"Ошибка при фильтрации продуктов: {e}")
        return {"products": []}
    
    
    

def get_one_product_and_similar(request, params):
    try:
        product_id = params.get("product_id")
        if not product_id:
            logger.warning("Отсутствует параметр product_id")
            return {"target_product": None, "similar_products": []}

        try:
            product_id = int(product_id)
        except ValueError:
            logger.warning(f"Недопустимый product_id: {product_id}")
            return {"target_product": None, "similar_products": []}

        target_product = Product.objects.filter(id=product_id).prefetch_related("features").first()
        if not target_product:
            logger.warning(f"Продукт с ID {product_id} не найден")
            return {"target_product": None, "similar_products": []}

        target_data = {
            "id": target_product.id,
            "name": target_product.name,
            "price": target_product.price,
            "discount": target_product.discount,
            "price_type": target_product.price_type,
            "selled": target_product.selled,
            "created_at": target_product.created_at,
            "updated_at": target_product.updated_at,
            "features": list(Features.objects.filter(product_id=target_product.id).values("key", "value"))
        }

        similar_products_qs = (
            Product.objects.filter(category=target_product.category)
            .exclude(id=product_id)
            .order_by("-selled")[:5]
            .prefetch_related("features")
            .values("id", "name", "price", "discount", "price_type", "selled", "created_at", "updated_at")
        )

        similar_products = []
        for product in similar_products_qs:
            product_data = dict(product)
            features = Features.objects.filter(product_id=product["id"]).values("key", "value")
            product_data["features"] = list(features)
            similar_products.append(product_data)

        return {
            "target_product": target_data,
            "similar_products": similar_products
        }

    except Exception as e:
        logger.error(f"Ошибка при получении продукта и похожих: {e}")
        return {"target_product": None, "similar_products": []}