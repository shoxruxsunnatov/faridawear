from django.urls import path

from sales.api import (
    SalesListViewAPI
)

app_name = "sales"

urlpatterns = [
    
    # APIs
    path("api/sales/", SalesListViewAPI.as_view(), name="sales_list_view_api"),
    path("api/sales/recent/", SalesListViewAPI.as_view(), name="recent_sales_list_view_api"),
]