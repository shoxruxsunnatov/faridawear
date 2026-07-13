from django.contrib import admin
from account.models import (
    User
)

class UserAdmin(admin.ModelAdmin):
    list_filter = [
        "role"
    ]

    search_fields = [
        "first_name",
        "last_name"
    ]
    filter_horizontal = [
        "user_permissions"
    ]
    
admin.site.register(User, UserAdmin)