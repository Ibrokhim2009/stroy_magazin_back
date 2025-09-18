



import re
from core.auth_models import User




EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'



def register(request, params):
    email = params.get('email', None)
    phone = params.get('phone', None)
    username = params.get('username', None)
    region = params.get('region', None)
    password = params.get('password', None)
    
    
    if None in [email, phone, username, region, password]:
        return {
            "response": {
                "error": "Заполните все поля"
            },
            "status": 400
        }
    if not re.match(EMAIL_REGEX, email):
        return {
            "response": {
                "error": "Некорректный email"
            },
            "status": 400
        }
        
    user = User.objects.filter(phone=phone)
    if user:
        return {
            "response": {
                "error": "Такой пользователь уже существует"
            },
            "status": 400
        }
    
    
    User.objects.create_user(
        phone=phone,
        username=username,
        password=password,
        email=email,
        place=region
    )
    return {
        "response":{
            'success': "Salomat"
            },
        "status": 200
        }















