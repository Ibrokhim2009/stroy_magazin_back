from methodism.main import METHODISM
from v1 import services
from v1.services.auth import authenticate_user

class MainView(METHODISM):
    file = services

    not_auth_methods = [
        "get_categories",
        "get_category",
        "login",
        "register",
        "refresh_access_token",
        "forgot_password",
        "reset_password",
        "verify_email",
    ]

    def get_token(self, request):
        user = authenticate_user(request)
        if user:
            return {"user": user} 
        return None