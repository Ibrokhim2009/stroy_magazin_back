import re
import jwt
import random
import string
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings
from core.auth_models import User, VerificationCode
from django.db import models
from methodism import generate_key
from django.contrib.auth import logout

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM

def generate_code():
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email, code, purpose):
    subject = 'Код подтверждения' if purpose == 'registration' else 'Код для сброса пароля'
    message = f'Ваш код: {code}'
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )

def generate_token(user_id, token_type='access', expires_in_minutes=15):
    if token_type == 'refresh':
        expires_in_minutes = 7 * 24 * 60 
    payload = {
        'user_id': user_id,
        'type': token_type,
        'exp': datetime.utcnow() + timedelta(minutes=expires_in_minutes),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

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
        
    if User.objects.filter(phone=phone).exists() or User.objects.filter(email=email).exists():
        return {
            "response": {
                "error": "Пользователь с таким телефоном или email уже существует"
            },
            "status": 400
        }
    
    user = User.objects.create_user(
        phone=phone,
        username=username,
        password=password,
        email=email,
        place=region,
        is_active=False
    )
    
    code = generate_code()
    VerificationCode.objects.create(
        user=user,
        code=code,
        expires_at=datetime.now().astimezone() + timedelta(minutes=10),
        purpose='registration'
    )
    send_verification_email(email, code, 'registration')
    
    return {
        "response": {
            "success": "Код подтверждения отправлен на ваш email"
        },
        "status": 200
    }

def verify_email(request, params):
    email = params.get('email', None)
    code = params.get('code', None)
    
    if None in [email, code]:
        return {
            "response": {
                "error": "Укажите email и код"
            },
            "status": 400   
        }
    
    try:
        user = User.objects.get(email=email)
        verification = VerificationCode.objects.filter(user=user, code=code, purpose='registration').latest('created_at')
        
        if not verification.is_valid():
            return {
                "response": {
                    "error": "Код истек"
                },
                "status": 400
            }
        
        user.is_active = True
        user.save()
        verification.delete() 
        
        access_token = generate_token(user.id)
        refresh_token = generate_token(user.id, 'refresh')
        
        return {
            "response": {
                "success": "Email подтвержден",
                "access_token": access_token,
                "refresh_token": refresh_token
            },
            "status": 200
        }
    
    except User.DoesNotExist:
        return {
            "response": {
                "error": "Пользователь не найден"
            },
            "status": 404
        }
    except VerificationCode.DoesNotExist:
        return {
            "response": {
                "error": "Неверный код"
            },
            "status": 400
        }

def login(request, params):
    username_or_phone = params.get('username', None)
    password = params.get('password', None)
    
    if None in [username_or_phone, password]:
        return {
            "response": {
                "error": "Заполните все поля"
            },
            "status": 400
        }
    
    try:
        user = User.objects.filter(username=username_or_phone).first()
        if not user:
            user = User.objects.filter(phone=username_or_phone).first()
        
        if not user or not user.check_password(password):
            return {
                "response": {
                    "error": "Неверные учетные данные"
                },
                "status": 401
            }
        
        if not user.is_active:
            return {
                "response": {
                    "error": "Подтвердите email перед входом"
                },
                "status": 403
            }
        
        access_token = generate_token(user.id)
        refresh_token = generate_token(user.id, 'refresh')
        
        return {
            "response": {
                "success": "Успешный вход",
                "access_token": access_token,
                "refresh_token": refresh_token
            },
            "status": 200
        }
    
    except Exception:
        return {
            "response": {
                "error": "Ошибка сервера"
            },
            "status": 500
        }

def forgot_password(request, params):
    email = params.get('email', None)
    
    if not email:
        return {
            "response": {
                "error": "Укажите email"
            },
            "status": 400
        }
    
    try:
        user = User.objects.get(email=email)
        code = generate_code()
        VerificationCode.objects.create(
            user=user,
            code=code,
            expires_at=datetime.now().astimezone() + timedelta(minutes=10),
            purpose='password_reset'
        )
        send_verification_email(email, code, 'password_reset')
        
        return {
            "response": {
                "success": "Код для сброса пароля отправлен на ваш email"
            },
            "status": 200
        }
    
    except User.DoesNotExist:
        return {
            "response": {
                "error": "Пользователь с таким email не найден"
            },
            "status": 404
        }

def reset_password(request, params):
    email = params.get('email', None)
    code = params.get('code', None)
    new_password = params.get('new_password', None)
    
    if None in [email, code, new_password]:
        return {
            "response": {
                "error": "Укажите email, код и новый пароль"
            },
            "status": 400
        }
    
    try:
        user = User.objects.get(email=email)
        verification = VerificationCode.objects.filter(user=user, code=code, purpose='password_reset').latest('created_at')
        
        if not verification.is_valid():
            return {
                "response": {
                    "error": "Код истек"
                },
                "status": 400
            }
        
        user.set_password(new_password)
        user.save()
        verification.delete()
        
        return {
            "response": {
                "success": "Пароль успешно изменен"
            },
            "status": 200
        }
    
    except User.DoesNotExist:
        return {
            "response": {
                "error": "Пользователь не найден"
            },
            "status": 404
        }
    except VerificationCode.DoesNotExist:
        return {
            "response": {
                "error": "Неверный код"
            },
            "status": 400
        }

def refresh_access_token(request, params):
    refresh_token = params.get('refresh_token', None)
    
    if not refresh_token:
        return {
            "response": {
                "error": "Требуется refresh token"
            },
            "status": 400
        }
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM], options={'verify_exp': False})
        
        if payload.get('type') != 'refresh':
            return {
                "response": {
                    "error": "Неверный тип токена"
                },
                "status": 401
            }
        
        user_id = payload.get('user_id')
        if not user_id:
            return {
                "response": {
                    "error": "Неверный токен"
                },
                "status": 401
            }
        
        user = User.objects.filter(id=user_id).first()
        if not user:
            return {
                "response": {
                    "error": "Пользователь не найден"
                },
                "status": 404
            }
        
        new_access_token = generate_token(user_id)
        
        return {
            "response": {
                "success": "Токен обновлен",
                "access_token": new_access_token
            },
            "status": 200
        }
    
    except jwt.ExpiredSignatureError:
        return {
            "response": {
                "error": "Refresh token истек"
            },
            "status": 401
        }
    except jwt.InvalidTokenError:
        return {
            "response": {
                "error": "Недействительный refresh token"
            },
            "status": 401
        }
        
def user_logout(request, params):
    if not request.user:
        return {
            "response": {"success": "Вы не авторизованы"},
            "status": 401
        }
    logout(request)
    return {
        "response": {"success": "Вы вышли из системы"},
        "status": 200
    }

def authenticate_user(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get('type') != 'access':
            return None
        user_id = payload.get('user_id')
        return User.objects.filter(id=user_id).first()
    except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
        return None