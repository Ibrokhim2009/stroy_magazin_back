
from methodism import METHODISM
from v1 import services








class MainView(METHODISM):
    file = services
    
    not_auth_methods = ['*']