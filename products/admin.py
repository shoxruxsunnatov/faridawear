from django.contrib import admin

from products.models import (
    Product
)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('serial', 'title', 'base_price', 'sale_price', 'stock', 'date_created')
    
    list_filter = ('date_created', 'organization')
    
    search_fields = ('serial', 'title', 'description')
    
    list_editable = ('base_price', 'sale_price', 'stock')