from django.urls import path

from products.views import (
    ProductsView
)
from products.api import (
    ProductsListViewAPI
)

app_name = "products"

urlpatterns = [
    path("products/", ProductsView.as_view(), name="products_list"),

    # APIs
    path("api/products/", ProductsListViewAPI.as_view(), name="products_list_api")
]