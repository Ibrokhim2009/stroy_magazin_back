from .auth import register

from methodism import custom_response

methods = dir()

def method_names(request, params) :
    natija = [x. replace("_", '.') for x in methods if "__" not in x and x != "custom_response"]
    return custom_response (True, data=natija)
