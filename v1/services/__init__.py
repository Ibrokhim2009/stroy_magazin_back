from .auth import register, login, refresh_access_token, verify_email, reset_password, forgot_password, user_logout
from .category import get_categories, get_category, create_category, update_category, delete_category
from methodism import custom_response
from .product import get_home_page_products, get_and_filter_products, get_one_product_and_similar
from .order import create_order
from .wishlist import add_wishlist, get_wishlist
from .basket import add_to_basket, get_basket
methods = dir()

def method_names(request, params) :
    natija = [x. replace("_", '.') for x in methods if "__" not in x and x != "custom_response"]
    return custom_response (True, data=natija)
