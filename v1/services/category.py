from core.models import Category
from v1.services.auth import authenticate_user

def get_categories(request, params):
    try:
        categories = Category.objects.all()

        def build_tree(cat):
            return {
                "id": cat.id,
                "name": cat.name,
                "parent": cat.parent.id if cat.parent else None,
                "image": cat.image.url if cat.image else None,
                "children": [build_tree(child) for child in cat.children.all()]
            }

        tree = [build_tree(cat) for cat in categories]

        return {
            "response": tree,
            "status": 200
        }

    except Exception as e:
        return {
            "response": {"error": f"Ошибка при получении категорий: {str(e)}"},
            "status": 500
        }

def create_category(request, params):
    user = authenticate_user(request)
    if not user:
        return {
            "response": {"error": "Требуется аутентификация"},
            "status": 401
        }

    name = params.get('name', None)
    parent_id = params.get('parent', None)
    image = request.FILES.get('image', None)

    if not name:
        return {
            "response": {"error": "Укажите название категории"},
            "status": 400
        }

    try:
        parent = Category.objects.filter(id=parent_id).first() if parent_id else None
        if Category.objects.filter(name=name).exists():
            return {
                "response": {"error": "Категория с таким именем уже существует"},
                "status": 400
            }

        category = Category.objects.create(
            name=name,
            parent=parent,
            image=image
        )
        return {
            "response": {"success": "Категория создана", "data": {
                'id': category.id,
                'name': category.name,
                'parent': category.parent.id if category.parent else None,
                'image': category.image.url if category.image else None,
                'children': []
            }},
            "status": 201
        }
    except Category.DoesNotExist:
        return {
            "response": {"error": "Родительская категория не найдена"},
            "status": 404
        }
    except Exception:
        return {
            "response": {"error": "Ошибка при создании категории"},
            "status": 500
        }

def get_category(request, params):
    try:
        category_id = params.get("id")
        if not category_id:
            return {
                "response": {"error": "Не передан id категории"},
                "status": 400
            }

        category = Category.objects.get(id=category_id)
        data = {
            'id': category.id,
            'name': category.name,
            'parent': category.parent.id if category.parent else None,
            'image': category.image.url if category.image else None,
            'children': [
                {
                    'id': child.id,
                    'name': child.name,
                    'parent': child.parent.id if child.parent else None,
                    'image': child.image.url if child.image else None
                }
                for child in category.children.all()
            ]
        }
        return {
            "response": data,
            "status": 200
        }

    except Category.DoesNotExist:
        return {
            "response": {"error": "Категория не найдена"},
            "status": 404
        }

def update_category(request, category_id, params):
    user = authenticate_user(request)
    if not user:
        return {
            "response": {"error": "Требуется аутентификация"},
            "status": 401
        }

    try:
        category = Category.objects.get(id=category_id)
        name = params.get('name', category.name)
        parent_id = params.get('parent', None)
        image = request.FILES.get('image', category.image)

        if name != category.name and Category.objects.filter(name=name).exclude(id=category_id).exists():
            return {
                "response": {"error": "Категория с таким именем уже существует"},
                "status": 400
            }

        parent = Category.objects.get(id=parent_id) if parent_id else None
        category.name = name
        category.parent = parent
        category.image = image
        category.save()

        return {
            "response": {"success": "Категория обновлена", "data": {
                'id': category.id,
                'name': category.name,
                'parent': category.parent.id if category.parent else None,
                'image': category.image.url if category.image else None,
                'children': []
            }},
            "status": 200
        }
    except Category.DoesNotExist:
        return {
            "response": {"error": "Категория не найдена"},
            "status": 404
        }
    except Exception:
        return {
            "response": {"error": "Ошибка при обновлении категории"},
            "status": 500
        }

def delete_category(request, category_id):
    user = authenticate_user(request)
    if not user:
        return {
            "response": {"error": "Требуется аутентификация"},
            "status": 401
        }

    try:
        category = Category.objects.get(id=category_id)
        if category.children.exists():
            return {
                "response": {"error": "Нельзя удалить категорию с дочерними элементами"},
                "status": 400
            }
        category.delete()
        return {
            "response": {"success": "Категория удалена"},
            "status": 200
        }
    except Category.DoesNotExist:
        return {
            "response": {"error": "Категория не найдена"},
            "status": 404
        }