from django.contrib import admin

from sales.models import (
    Sale,
    SaleItem,
    Payment
)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'sale_total', 'profit', 'debt', 'date_created')
    
    list_filter = ('date_created', 'organization')
    
    search_fields = ('id',)
    
    list_editable = ()


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'sale', 'organization', 'sale_price', 'date_created')
    
    list_filter = ('date_created', 'organization')
    
    search_fields = ('id',)
    
    list_editable = ()


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount', 'profit', 'method', 'organization', 'date_created')
    
    list_filter = ('date_created', 'organization')
    
    search_fields = ('id',)
    
    list_editable = ()