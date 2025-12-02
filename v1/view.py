from methodism.main import METHODISM
from v1 import services
from v1.services.auth import authenticate_user
from rest_framework.views import APIView
class MainView(METHODISM):
    file = services
    not_auth_methods = ["*"]

    def get_serializer_class(self):
        # DRF перестанет думать что сериалайзер нужен
        return super(APIView, self).get_serializer_class()

    def get_serializer(self, *args, **kwargs):
        # DRF перестанет пытаться создать сериализатор
        return None

    def get_token(self, request):
        user = authenticate_user(request)
        if user:
            return {"user": user}
        return None
