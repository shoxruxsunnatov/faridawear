from django.contrib import admin

from main.models import (
    Organization,
    Group,
)

admin.site.register(Organization)
admin.site.register(Group)
